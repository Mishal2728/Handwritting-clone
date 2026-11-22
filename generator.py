import os
import glob
import random
import re
import io
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from PIL import Image

# ══════════════════════════════════════════════════════════════════════════
#  1. CHARACTER NORMALIZATION
# ══════════════════════════════════════════════════════════════════════════

CHAR_REPLACEMENTS = {
    '–': '-',   # en-dash
    '—': '-',   # em-dash
    '―': '-',   # horizontal bar
    '−': '-',   # minus sign
    '“': '"',   # left double quote
    '”': '"',   # right double quote
    '„': '"',   # low double quote
    '‘': "'",   # left single quote
    '’': "'",   # right single quote
    '‚': "'",   # low single quote
    '`': "'",   # backtick
    '´': "'",   # acute accent
    '…': '...', # ellipsis
    '\u00a0': ' ',  # non-breaking space
    '\u200b': '',   # zero-width space
    '\u202f': ' ',  # narrow no-break space
    '\ufeff': '',   # zero width no-break space / BOM
    '•': '-',   # bullet point
    '‣': '>',
    '⁃': '-',
}

def normalize_text(text: str) -> str:
    """Replaces unsupported unicode symbols with matching ASCII glyphs."""
    for orig, repl in CHAR_REPLACEMENTS.items():
        text = text.replace(orig, repl)
    return text


# ══════════════════════════════════════════════════════════════════════════
#  2. CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class HandwritingConfig:
    """Dynamic configuration values for layout, styling, and human-like randomness."""

    # Margins and Line Geometry
    margin_left: int = 230
    margin_right: int = 40
    margin_top: int = 60
    margin_bottom: int = 60
    line_height: int = 110
    char_height: int = 160

    # Hanging margin start for $number
    outdent_margin_left: int = 180

    # Human-like random line indent variation
    random_line_indent: int = 14

    # Font sizing & spacing
    font_scale: float = 0.70
    char_spacing_offset: int = -2
    random_spacing: int = 1

    # Human jitter & rotation
    random_x_offset: int = 2
    random_y_offset: int = 3
    random_rotation: float = 1.6
    enable_pressure: bool = True
    enable_fatigue: bool = True

    # Paper Background: 0 = random mix among bg1-bg4, or 1..4 for specific bg
    background_choice: int = 0

    # Base Ink Colors (RGB)
    default_ink_color: Tuple[int, int, int] = (15, 15, 20)      # Dark ink / black
    quote_ink_color: Tuple[int, int, int] = (25, 75, 180)       # Blue pen for quotes/highlights

    @classmethod
    def from_dict(cls, data: dict) -> "HandwritingConfig":
        cfg = cls()
        if not data:
            return cfg

        for key, val in data.items():
            if hasattr(cfg, key):
                target_type = type(getattr(cfg, key))
                try:
                    if target_type == Tuple[int, int, int] or key.endswith('_color'):
                        if isinstance(val, (list, tuple)) and len(val) >= 3:
                            setattr(cfg, key, (int(val[0]), int(val[1]), int(val[2])))
                        elif isinstance(val, str) and val.startswith('#'):
                            # Hex to RGB
                            h = val.lstrip('#')
                            if len(h) == 6:
                                rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                                setattr(cfg, key, rgb)
                    elif target_type == float:
                        setattr(cfg, key, float(val))
                    elif target_type == int:
                        setattr(cfg, key, int(val))
                    elif target_type == bool:
                        setattr(cfg, key, bool(val))
                except (ValueError, TypeError):
                    pass
        return cfg


# ══════════════════════════════════════════════════════════════════════════
#  3. GLYPH & ASSET MANAGER
# ══════════════════════════════════════════════════════════════════════════

class GlyphManager:
    """Loads and caches glyph images from the font directory with variation support."""

    def __init__(self, config: HandwritingConfig, font_dir: str = "font"):
        self.config = config
        self.font_dir = font_dir
        self._char_variations: Dict[int, List[Image.Image]] = {}
        self._load_all_glyphs()

    def _load_all_glyphs(self):
        """Pre-index glyph images from disk for fast rendering."""
        pattern = os.path.join(self.font_dir, "*.png")
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            if filename.startswith("bg"):
                continue

            name_part = filename.split(".")[0]
            code_str = name_part.split("_")[0]
            if code_str.isdigit():
                code = int(code_str)
                try:
                    img = Image.open(filepath).copy()
                    if code not in self._char_variations:
                        self._char_variations[code] = []
                    self._char_variations[code].append(img)
                except Exception:
                    pass

    def load_char(self, code: int) -> Optional[Image.Image]:
        variants = self._char_variations.get(code)
        if variants:
            return random.choice(variants).copy()
        return None

    def prepare_char(
        self,
        code: int,
        color: Tuple[int, int, int],
        fatigue_rot: float = 0.0,
        opacity_factor: float = 1.0,
    ) -> Optional[Image.Image]:
        img = self.load_char(code)
        if img is None:
            return None

        # Subtle micro-scale variation per stroke
        micro_scale = self.config.font_scale * random.uniform(0.97, 1.03)
        new_w = max(1, int(img.width * micro_scale))
        new_h = max(1, int(img.height * micro_scale))
        img = img.resize((new_w, new_h), resample=Image.LANCZOS)

        # Micro-rotation
        max_rot = self.config.random_rotation + fatigue_rot
        angle = random.uniform(-max_rot, max_rot) if max_rot > 0 else 0.0
        if abs(angle) > 0.05:
            img = img.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
        else:
            img = img.convert("RGBA")

        # Color jitter for ink feel
        r_jitter = min(255, max(0, color[0] + random.randint(-5, 5)))
        g_jitter = min(255, max(0, color[1] + random.randint(-5, 5)))
        b_jitter = min(255, max(0, color[2] + random.randint(-5, 5)))
        final_rgb = (r_jitter, g_jitter, b_jitter)

        alpha = img.split()[3]
        if opacity_factor < 1.0:
            alpha = alpha.point(lambda p: int(p * opacity_factor))

        solid = Image.new("RGBA", img.size, final_rgb + (255,))
        solid.putalpha(alpha)
        return solid

    def char_pixel_width(self, ch: str) -> int:
        img = self.load_char(ord(ch))
        base_w = (
            max(1, int(20 * self.config.font_scale))
            if img is None
            else max(1, int(img.width * self.config.font_scale))
        )
        return max(1, base_w + self.config.char_spacing_offset)

    def measure_word_width(self, word: str) -> int:
        clean_word = word.replace("|", "")
        return sum(self.char_pixel_width(ch) for ch in clean_word)

    def measure_line_width(self, line: str) -> int:
        clean_line = line.replace("|", "")
        return sum(self.char_pixel_width(ch) for ch in clean_line)


# ══════════════════════════════════════════════════════════════════════════
#  4. RENDER ENGINE & PAGINATION
# ══════════════════════════════════════════════════════════════════════════

def tokenise_line(line: str) -> List[Tuple[str, str]]:
    tokens = []
    i = 0
    while i < len(line):
        if line[i] in (" ", "\t"):
            j = i
            while j < len(line) and line[j] in (" ", "\t"):
                j += 1
            tokens.append(("space", line[i:j]))
            i = j
        else:
            j = i
            while j < len(line) and line[j] not in (" ", "\t"):
                j += 1
            tokens.append(("word", line[i:j]))
            i = j
    return tokens


class DocumentRenderer:
    """Draws realistic handwritten pages onto notebook backgrounds."""

    def __init__(
        self,
        config: HandwritingConfig,
        glyph_mgr: GlyphManager,
        font_dir: str = "font",
        max_pages: Optional[int] = None,
    ):
        self.cfg = config
        self.glyph_mgr = glyph_mgr
        self.font_dir = font_dir
        self.max_pages = max_pages

        self.bg_templates: Dict[int, Image.Image] = {}
        for i in range(1, 5):
            bg_p = os.path.join(self.font_dir, f"bg{i}.png")
            if os.path.exists(bg_p):
                try:
                    self.bg_templates[i] = Image.open(bg_p).copy()
                except Exception:
                    pass

        if not self.bg_templates:
            # Fallback blank lined paper if background pngs not found
            fallback = Image.new("RGBA", (1654, 2339), (252, 250, 242, 255))
            self.bg_templates[1] = fallback

        first_bg = self._get_bg_image(0)
        self.page_w = first_bg.width
        self.page_h = first_bg.height
        self.printable_right = self.page_w - self.cfg.margin_right
        self.printable_width = self.printable_right - self.cfg.margin_left

        self.pages: List[Image.Image] = []
        self.current_page = first_bg.copy().convert("RGBA")
        self.current_line_left = self.get_random_margin()
        self.cursor_x = self.current_line_left
        self.cursor_y = self.cfg.margin_top
        self.inside_quotes = False

        self.current_page_idx = 0
        self.word_counter = 0
        self.current_pressure = 1.0

    def _get_bg_image(self, page_index: int) -> Image.Image:
        if self.cfg.background_choice in self.bg_templates:
            return self.bg_templates[self.cfg.background_choice]
        # Choose randomly among available
        available_keys = list(self.bg_templates.keys())
        choice = random.choice(available_keys)
        return self.bg_templates[choice]

    def get_random_margin(self) -> int:
        if self.cfg.random_line_indent <= 0:
            return self.cfg.margin_left
        return self.cfg.margin_left + random.randint(
            -self.cfg.random_line_indent, self.cfg.random_line_indent
        )

    def check_line_overflow(self, width_needed: int) -> bool:
        return self.cursor_x + width_needed > (self.printable_right + 15)

    def check_page_overflow(self) -> bool:
        return self.cursor_y + self.cfg.char_height > (
            self.page_h - self.cfg.margin_bottom
        )

    def create_new_page(self) -> bool:
        self.pages.append(self.current_page)
        self.current_page_idx += 1

        if self.max_pages and len(self.pages) >= self.max_pages:
            return False

        next_bg = self._get_bg_image(self.current_page_idx)
        self.current_page = next_bg.copy().convert("RGBA")
        self.current_line_left = self.get_random_margin()
        self.cursor_x = self.current_line_left
        self.cursor_y = self.cfg.margin_top + random.randint(-2, 2)
        return True

    def move_to_next_line(self) -> bool:
        self.cursor_y += self.cfg.line_height
        self.current_line_left = self.get_random_margin()
        self.cursor_x = self.current_line_left
        if self.check_page_overflow():
            return self.create_new_page()
        return True

    def ensure_page_has_room(self) -> bool:
        if self.check_page_overflow():
            return self.create_new_page()
        return True

    def render_char_at_cursor(self, ch: str, color: Tuple[int, int, int]):
        fatigue_rot = (
            min(2.0, self.current_page_idx * 0.35)
            if self.cfg.enable_fatigue
            else 0.0
        )

        char_img = self.glyph_mgr.prepare_char(
            ord(ch),
            color,
            fatigue_rot=fatigue_rot,
            opacity_factor=self.current_pressure,
        )
        if char_img is None:
            return

        x_jit = (
            random.randint(-self.cfg.random_x_offset, self.cfg.random_x_offset)
            if self.cfg.random_x_offset > 0
            else 0
        )
        y_jit = (
            random.randint(-self.cfg.random_y_offset, self.cfg.random_y_offset)
            if self.cfg.random_y_offset > 0
            else 0
        )
        paste_x = self.cursor_x + x_jit
        paste_y = max(self.cfg.margin_top, self.cursor_y + y_jit)

        if ch in ("=", "-", "+"):
            paste_y = self.cursor_y + (self.cfg.line_height - char_img.height) // 2
        elif ch == ":":
            paste_y = self.cursor_y + int(self.cfg.line_height * 0.28)

        self.current_page.paste(char_img, (paste_x, paste_y), char_img)

        spacing_jitter = (
            random.randint(-self.cfg.random_spacing, self.cfg.random_spacing)
            if self.cfg.random_spacing > 0
            else 0
        )
        step_x = char_img.width + self.cfg.char_spacing_offset + spacing_jitter
        self.cursor_x += max(1, step_x)

    def render_word_with_wrapping(
        self, word: str, force_color: Optional[Tuple[int, int, int]] = None
    ) -> bool:
        if self.cfg.enable_pressure:
            self.word_counter += 1
            if self.word_counter % random.randint(4, 9) == 0:
                self.current_pressure = random.uniform(0.86, 1.0)

        word_width = self.glyph_mgr.measure_word_width(word)

        if (
            self.check_line_overflow(word_width)
            and self.cursor_x != self.current_line_left
        ):
            if not self.move_to_next_line():
                return False

        for ch in word:
            if ch == "|":
                self.inside_quotes = not self.inside_quotes
                continue

            color = (
                force_color
                if force_color is not None
                else (self.cfg.quote_ink_color if self.inside_quotes else self.cfg.default_ink_color)
            )
            self.render_char_at_cursor(ch, color)
        return True

    def render_whitespace_run(self, run: str, suppress: bool) -> Tuple[bool, bool]:
        """Returns (suppress, can_continue)."""
        for ch in run:
            if suppress:
                continue

            base_w = (
                self.glyph_mgr.char_pixel_width(" ") * 4
                if ch == "\t"
                else self.glyph_mgr.char_pixel_width(" ")
            )
            w = max(4, base_w + random.randint(-1, 2))
            if self.check_line_overflow(w):
                if not self.move_to_next_line():
                    return (True, False)
                suppress = True
                continue

            self.cursor_x += w
        return (suppress, True)

    def render_centred_line(self, line: str) -> bool:
        if not self.ensure_page_has_room():
            return False

        line_width = self.glyph_mgr.measure_line_width(line)

        if line_width <= self.printable_width:
            centre_x = (
                self.cfg.margin_left + (self.printable_width - line_width) // 2
            )
            self.cursor_x = max(self.cfg.margin_left, centre_x)
            for ch in line:
                self.render_char_at_cursor(ch, self.cfg.quote_ink_color)
            return self.move_to_next_line()
        else:
            self.current_line_left = self.get_random_margin()
            self.cursor_x = self.current_line_left
            suppress = False
            for tok_type, tok_val in tokenise_line(line):
                if tok_type == "space":
                    suppress, ok = self.render_whitespace_run(tok_val, suppress)
                    if not ok:
                        return False
                else:
                    if not self.render_word_with_wrapping(
                        tok_val, force_color=self.cfg.quote_ink_color
                    ):
                        return False
                    suppress = False
            return self.move_to_next_line()

    def process_text(self, text: str):
        lines = text.split("\n")
        for line in lines:
            if not self.ensure_page_has_room():
                break

            if line == "":
                self.cursor_y += self.cfg.line_height
                self.current_line_left = self.get_random_margin()
                self.cursor_x = self.current_line_left
                if self.check_page_overflow():
                    if not self.create_new_page():
                        break
                continue

            stripped = line.strip()

            # Centred title syntax: ||Title||
            if (
                stripped.startswith("||")
                and stripped.endswith("||")
                and len(stripped) >= 4
            ):
                if not self.render_centred_line(stripped[2:-2]):
                    break
                continue

            # Outdented syntax: $1) or $Prefix
            if line.startswith("$"):
                tokens = tokenise_line(line[1:])
                if tokens:
                    first_token_type, first_token_val = tokens[0]
                    self.cursor_x = self.cfg.outdent_margin_left + random.randint(-3, 3)

                    for ch in first_token_val:
                        col = (
                            self.cfg.quote_ink_color
                            if self.inside_quotes
                            else self.cfg.default_ink_color
                        )
                        self.render_char_at_cursor(ch, col)

                    self.current_line_left = self.get_random_margin()
                    self.cursor_x = max(self.cursor_x, self.current_line_left)
                    tokens = tokens[1:]

                    if tokens and tokens[0][0] == "space":
                        tokens = tokens[1:]

                    suppress = False
                    stopped = False
                    for tok_type, tok_val in tokens:
                        if tok_type == "space":
                            suppress, ok = self.render_whitespace_run(tok_val, suppress)
                            if not ok:
                                stopped = True
                                break
                        else:
                            if not self.render_word_with_wrapping(tok_val):
                                stopped = True
                                break
                            suppress = False

                    if stopped or not self.move_to_next_line():
                        break
                    continue

            # Regular Left-aligned lines
            self.current_line_left = self.get_random_margin()
            self.cursor_x = self.current_line_left
            suppress = False
            stopped = False

            for tok_type, tok_val in tokenise_line(line):
                if tok_type == "space":
                    suppress, ok = self.render_whitespace_run(tok_val, suppress)
                    if not ok:
                        stopped = True
                        break
                else:
                    if not self.render_word_with_wrapping(tok_val):
                        stopped = True
                        break
                    suppress = False

            if stopped or not self.move_to_next_line():
                break

        if self.current_page not in self.pages:
            self.pages.append(self.current_page)


# ══════════════════════════════════════════════════════════════════════════
#  5. TOP-LEVEL GENERATOR API
# ══════════════════════════════════════════════════════════════════════════

class HandwritingService:
    """High-level generator interface for rendering text into images and PDF/ZIP."""

    def __init__(self, font_dir: str = "font"):
        self.font_dir = font_dir
        # Reusable glyph manager baseline
        self.baseline_config = HandwritingConfig()
        self.glyph_mgr = GlyphManager(self.baseline_config, font_dir=self.font_dir)

    def render(
        self,
        text: str,
        config: Optional[HandwritingConfig] = None,
        max_pages: Optional[int] = None,
        auto_normalize: bool = True,
    ) -> List[Image.Image]:
        if config is None:
            config = self.baseline_config

        if auto_normalize:
            text = normalize_text(text)

        # Update glyph manager's config reference
        self.glyph_mgr.config = config

        renderer = DocumentRenderer(
            config,
            self.glyph_mgr,
            font_dir=self.font_dir,
            max_pages=max_pages,
        )
        renderer.process_text(text)
        return renderer.pages

    def export_pdf(self, pages: List[Image.Image]) -> bytes:
        if not pages:
            return b""
        rgb_pages = [page.convert("RGB") for page in pages]
        buf = io.BytesIO()
        rgb_pages[0].save(
            buf,
            format="PDF",
            save_all=True,
            append_images=rgb_pages[1:],
            resolution=100.0,
        )
        return buf.getvalue()

    def export_zip(self, pages: List[Image.Image], prefix: str = "handwriting_page") -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(pages, start=1):
                img_buf = io.BytesIO()
                page.convert("RGB").save(img_buf, format="PNG")
                zf.writestr(f"{prefix}_{i}.png", img_buf.getvalue())
        return buf.getvalue()
