import os
import sys
import time
import uuid
import io
import base64
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, send_file, Response
from PIL import Image

from generator import HandwritingService, HandwritingConfig

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# Global handwriting service instance (loads glyphs once into memory)
SERVICE = HandwritingService(font_dir="font")

# In-memory storage for active render sessions
# session_id -> { "pages": [Image], "created_at": float, "config": dict, "text": str }
SESSIONS: Dict[str, Dict[str, Any]] = {}
MAX_SESSION_AGE_SECONDS = 3600  # Clean up sessions older than 1 hour


def cleanup_old_sessions():
    """Removes expired sessions to keep memory usage low."""
    now = time.time()
    expired = [
        sid for sid, data in SESSIONS.items()
        if now - data.get("created_at", 0) > MAX_SESSION_AGE_SECONDS
    ]
    for sid in expired:
        del SESSIONS[sid]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sample', methods=['GET'])
def get_sample_text():
    sample_path = "test.txt"
    if os.path.exists(sample_path):
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                content = f.read()
            return jsonify({"status": "success", "text": content})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # Fallback sample if test.txt is absent
    fallback = (
        "Name:|Alex Morgan|\n"
        "Reg no:|REG-2026-0042|\n"
        "Subject:|Software Project Management|\n"
        "Date:|21.11.2026|\n\n"
        "||SECTION - A||\n\n"
        "$1) Explain Software Engineering layers:\n"
        "|Software engineering is a layered technology with Process, Methods, and Tools.|\n"
    )
    return jsonify({"status": "success", "text": fallback})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    try:
        content = uploaded_file.read().decode('utf-8', errors='replace')
        return jsonify({
            "status": "success",
            "filename": uploaded_file.filename,
            "text": content,
            "length": len(content)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to read file: {e}"}), 500


@app.route('/api/render', methods=['POST'])
def render_handwriting():
    cleanup_old_sessions()

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"status": "error", "message": "Text cannot be empty"}), 400

    cfg_dict = data.get("config", {})
    config = HandwritingConfig.from_dict(cfg_dict)

    preview_only = bool(data.get("preview_only", False))
    max_pages = 1 if preview_only else data.get("max_pages")
    auto_normalize = bool(data.get("auto_normalize", True))

    start_time = time.time()
    try:
        pages = SERVICE.render(
            text=text,
            config=config,
            max_pages=max_pages,
            auto_normalize=auto_normalize,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Rendering error: {e}"}), 500

    elapsed = round(time.time() - start_time, 2)
    session_id = str(uuid.uuid4())

    thumb_cache = {}
    page_cache = {}
    page_urls = []

    for i, page in enumerate(pages, 1):
        # Ultra-fast downsample (width 140, Image.BOX, JPEG q=60) ~2.9 KB
        ratio = 140 / float(page.width)
        thumb_size = (140, int(page.height * ratio))
        thumb = page.resize(thumb_size, resample=Image.BOX)
        t_buf = io.BytesIO()
        thumb.convert("RGB").save(t_buf, format="JPEG", quality=60)
        t_bytes = t_buf.getvalue()
        thumb_cache[i] = t_bytes
        b64_thumb = "data:image/jpeg;base64," + base64.b64encode(t_bytes).decode("ascii")

        page_urls.append({
            "page_num": i,
            "url": f"/api/page/{session_id}/{i}",
            "thumb_url": f"/api/page/{session_id}/{i}?thumb=1",
            "thumb_data": b64_thumb
        })

    # Pre-cache Page 1 preview for instant first render
    if pages:
        p1_buf = io.BytesIO()
        pages[0].convert("RGB").save(p1_buf, format="JPEG", quality=80)
        page_cache[1] = p1_buf.getvalue()

    SESSIONS[session_id] = {
        "pages": pages,
        "created_at": time.time(),
        "config": cfg_dict,
        "text_length": len(text),
        "thumb_cache": thumb_cache,
        "page_cache": page_cache
    }

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "total_pages": len(pages),
        "render_time_sec": elapsed,
        "pages": page_urls,
        "is_preview": preview_only
    })


@app.route('/api/page/<session_id>/<int:page_num>')
def get_page(session_id: str, page_num: int):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session expired or not found"}), 404

    pages = session["pages"]
    if page_num < 1 or page_num > len(pages):
        return jsonify({"status": "error", "message": "Invalid page number"}), 404

    page = pages[page_num - 1]
    is_thumb = request.args.get('thumb') == '1'
    cache_key = "thumb_cache" if is_thumb else "page_cache"
    cache = session.setdefault(cache_key, {})

    if page_num in cache:
        buf = io.BytesIO(cache[page_num])
    else:
        buf = io.BytesIO()
        if is_thumb:
            ratio = 140 / float(page.width)
            thumb_size = (140, int(page.height * ratio))
            thumb = page.resize(thumb_size, resample=Image.BOX)
            thumb.convert("RGB").save(buf, format="JPEG", quality=60)
        else:
            page.convert("RGB").save(buf, format="JPEG", quality=80)

        cache[page_num] = buf.getvalue()
        buf.seek(0)

    response = send_file(buf, mimetype="image/jpeg")
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.route('/api/download/pdf/<session_id>')
def download_pdf(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session expired or not found"}), 404

    pages = session["pages"]
    pdf_bytes = SERVICE.export_pdf(pages)

    filename = request.args.get("name", "handwritten_document.pdf")
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/download/zip/<session_id>')
def download_zip(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session expired or not found"}), 404

    pages = session["pages"]
    zip_bytes = SERVICE.export_zip(pages, prefix="page")

    filename = request.args.get("name", "handwritten_pages.zip")
    if not filename.endswith(".zip"):
        filename += ".zip"

    return send_file(
        io.BytesIO(zip_bytes),
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/download/page/<session_id>/<int:page_num>')
def download_single_page(session_id: str, page_num: int):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": "Session expired or not found"}), 404

    pages = session["pages"]
    if page_num < 1 or page_num > len(pages):
        return jsonify({"status": "error", "message": "Invalid page number"}), 404

    page = pages[page_num - 1]
    buf = io.BytesIO()
    page.convert("RGB").save(buf, format="PNG")
    buf.seek(0)

    filename = f"handwritten_page_{page_num}.png"
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5050))
    print(f"\n==================================================")
    print(f"  ✍️ Handwriting Studio is running!")
    print(f"  Open your browser at: http://localhost:{port}")
    print(f"==================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
