# ✍️ Handwriting Studio — Professional Digital to Realistic Handwriting

A modern, studio-grade Web Application that converts digital text into authentic human handwriting on ruled assignment and examination notebook papers.

Designed with the craftsmanship, visual quality, and ergonomics of products like **Linear**, **Raycast**, and **Vercel**.

---

## 🚀 Quick Launch (எப்படி துவக்குவது?)

### Method 1: Double-Click Launcher (Recommended on macOS)
Finder-ல் **`start.command`** file-ஐ double-click செய்யவும்!
- இது தேவையான dependencies (Flask, Pillow)-ஐ தானாகவே verify செய்து கொள்ளும்.
- Server-ஐ துவக்கி உங்கள் default browser-ல் (`http://localhost:5050`) தானாகவே Open செய்யும்.

### Method 2: Terminal Execution
```bash
python3 app.py
```
Browser-ல் [http://localhost:5050](http://localhost:5050) திறந்து பயன்படுத்தலாம்.

---

## 🎨 UI/UX Redesign Highlights (வடிவமைப்பு சிறப்பம்சங்கள்)

1. **Obsidian Dark & Clean Light Themes**:
   - Refined typography (Inter & JetBrains Mono) with precise letter spacing and tabular metrics.
   - Glassmorphic floating toolbars and subtle border hierarchy.
   - 100% vector SVG icons with Retina crispness.

2. **Ergonomic Workspace Layout**:
   - **Collapsible Inspector / Style Drawer (`⌥S`)**: தேவைக்கேற்ப பக்கவாட்டு Settings Panel-ஐ மறைத்து / திறந்து Editor & Preview-க்கு அதிக இடம் ஒதுக்கலாம்.
   - **Monospace Code Editor**: Line number gutter, Tab key indentation, live metrics (words, chars, lines, page estimates), மற்றும் Drag-and-Drop file import zone.
   - **Studio Canvas**: Subtle dot-grid backdrop, multi-layer natural paper shadow, மற்றும் floating zoom dock.

3. **Handwriting Realism & Style Controls**:
   - **Presets**: Segmented pill tabs (`Exam`, `Assignment`, `Royal`, `Compact`).
   - **Curated Ink Swatches**: Hex-preview color pickers for Base Ink and Highlight Ink.
   - **Paper Selection**: Auto Random (Natural notebook mix) or specific ruled sheets 1–4.
   - **Micro Physics**: Slant jitter (0–3.5°), uneven left margin variations (0–28px), pen pressure simulation, and multi-page hand fatigue drift.

4. **Interactive Syntax & Formatting Tools**:
   - `||SECTION - A||` → Centered heading in highlight ink.
   - `$1) Question` → Margin hanging indent for question numbers.
   - `|Key Phrase|` → Toggle secondary / highlight ink.

5. **Multi-Page Viewing & High-Res Export**:
   - Real-time filmstrip thumbnail carousel with active focus rings.
   - Interactive zoom controls (`−`, `100%`, `+`, `↺ Fit`, `⛶ Fullscreen Lightbox`).
   - 1-Click Multi-Page PDF Download (`⌘S`).
   - ZIP Archive of all pages as PNG.
   - Individual PNG page export.

---

## ⌨️ Keyboard Shortcuts (விசைப்பலகை குறுக்குவழிகள்)

| Shortcut | செயல்பாடு |
|---|---|
| <kbd>⌘</kbd> + <kbd>Enter</kbd> / <kbd>Ctrl</kbd> + <kbd>Enter</kbd> | Generate All Pages |
| <kbd>⌘</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> | Quick Preview (Page 1) |
| <kbd>⌘</kbd> + <kbd>S</kbd> / <kbd>Ctrl</kbd> + <kbd>S</kbd> | Download Multi-Page PDF |
| <kbd>⌘</kbd> + <kbd>K</kbd> / <kbd>Ctrl</kbd> + <kbd>K</kbd> | Open Syntax Guide Modal |
| <kbd>⌥</kbd> + <kbd>S</kbd> | Toggle Styles Sidebar |
| <kbd>←</kbd> / <kbd>→</kbd> | Previous / Next Page in Canvas |
| <kbd>Esc</kbd> | Close Modals / Fullscreen Lightbox |

---

## 📂 Project Architecture

```
├── start.command         # macOS double-clickable launcher script
├── app.py                # Production Flask web server & REST APIs
├── generator.py          # Fast glyph caching & rendering engine (PDF/ZIP/PNG)
├── templates/
│   └── index.html        # High-craft studio frontend (Responsive, Inter + SVGs)
├── font/                 # Character glyph PNGs & Ruled paper backgrounds (bg1-bg4)
├── test.txt              # Sample assignment text
└── README.md             # Documentation & cheat sheet
```
