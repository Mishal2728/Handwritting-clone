import os
import glob
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from PIL import Image

# ══════════════════════════════════════════════════════════════════════════
#  1. CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class Config:
    """Holds all global configuration values and layout constants."""

    # Layout Margins
    margin_left: int = 200
    margin_right: int = 30
    margin_top: int = 30
    margin_bottom: int = 30
    line_height: int = 110
    char_height: int = 100

    # Hanging margin start for $number
    outdent_margin_left: int = 40

    # Font and Randomization Baseline
    font_scale: float = 0.8
    random_x_offset: int = 1
    random_y_offset: int = 2
    random_rotation: float = 1.2
    random_spacing: int = 1 

    # Letter spacing control
    char_spacing_offset: int = -2

    # Base Ink Colors
    default_ink_color: Tuple[int, int, int] = (15, 15, 20)
    quote_ink_color: Tuple[int, int, int] = (25, 75, 180)


# ══════════════════════════════════════════════════════════════════════════
#  2. GLYPH & ASSET MANAGER
# ══════════════════════════════════════════════════════════════════════════


class GlyphManager:

    def __init__(self, config: Config):
        self.config = config
        self._char_variations: Dict[int, List[Image.Image]] = {}

    def load_char(self, code: int) -> Optional[Image.Image]:
        if code in self._char_variations:
            variants = self._char_variations[code]
            if variants:
                return random.choice(variants).copy()
            return None

        matching_files = glob.glob(f"font/{code}.png") + glob.glob(f"font/{code}_*.png")

        variants = []
        for path in matching_files:
            try:
                variants.append(Image.open(path).copy())
            except Exception:
                pass

        if variants:
            self._char_variations[code] = variants
            return random.choice(variants).copy()
        else:
            print(f"  [warn] No image for character '{chr(code)}' (code {code})")
            self._char_variations[code] = []
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

        micro_scale = self.config.font_scale * random.uniform(0.97, 1.03)
        new_w = max(1, int(img.width * micro_scale))
        new_h = max(1, int(img.height * micro_scale))
        img = img.resize((new_w, new_h), resample=Image.LANCZOS)

        max_rot = self.config.random_rotation + fatigue_rot
        angle = random.uniform(-max_rot, max_rot)
        img = img.convert("RGBA").rotate(
            angle, expand=True, resample=Image.BICUBIC
        )

        r_jitter = min(255, max(0, color[0] + random.randint(-6, 6)))
        g_jitter = min(255, max(0, color[1] + random.randint(-6, 6)))
        b_jitter = min(255, max(0, color[2] + random.randint(-6, 6)))
        final_rgb = (r_jitter, g_jitter, b_jitter)

        alpha = img.split()[3]
        if opacity_factor < 1.0:
            alpha = alpha.point(lambda p: int(p * opacity_factor))

        solid = Image.new("RGBA", img.size, final_rgb + (255,))
        solid.putalpha(alpha)
        return solid

    def char_pixel_width(self, ch: str) -> int:
        img = self.load_char(ord(ch))
        base_w = max(1, int(20 * self.config.font_scale)) if img is None else max(1, int(img.width * self.config.font_scale))
        return max(1, base_w + self.config.char_spacing_offset)

    def measure_word_width(self, word: str) -> int:
        return sum(self.char_pixel_width(ch) for ch in word)

    def measure_line_width(self, line: str) -> int:
        return sum(self.char_pixel_width(ch) for ch in line)


# ══════════════════════════════════════════════════════════════════════════
#  3. RENDER ENGINE & PAGINATION
# ══════════════════════════════════════════════════════════════════════════


class DocumentRenderer:

    def __init__(self, config: Config, glyph_mgr: GlyphManager):
        self.cfg = config
        self.glyph_mgr = glyph_mgr

        bg_choice = random.randint(1, 4)
        bg_path = f"font/bg{bg_choice}.png"
        try:
            self.bg_template = Image.open(bg_path)
        except FileNotFoundError:
            print(f"Could not find background: {bg_path}")
            sys.exit(1)

        self.page_w = self.bg_template.width
        self.page_h = self.bg_template.height
        self.printable_right = self.page_w - self.cfg.margin_right
        self.printable_width = self.printable_right - self.cfg.margin_left

        self.pages: List[Image.Image] = []
        self.current_page = self.bg_template.copy().convert("RGBA")
        self.cursor_x = self.cfg.margin_left
        self.cursor_y = self.cfg.margin_top
        self.inside_quotes = False

        self.current_page_idx = 0
        self.word_counter = 0
        self.current_pressure = 1.0

    def next_char_color(self, ch: str) -> Tuple[int, int, int]:
        if ch == "|":
            self.inside_quotes = not self.inside_quotes
            return self.cfg.quote_ink_color
        return (
            self.cfg.quote_ink_color
            if self.inside_quotes
            else self.cfg.default_ink_color
        )

    def check_line_overflow(self, width_needed: int) -> bool:
        return self.cursor_x + width_needed > self.printable_right

    def check_page_overflow(self) -> bool:
        return self.cursor_y + self.cfg.char_height > (
            self.page_h - self.cfg.margin_bottom
        )

    def create_new_page(self):
        self.pages.append(self.current_page)
        self.current_page_idx += 1
        next_choice = random.randint(1, 4)
        next_path = f"font/bg{next_choice}.png"
        try:
            next_bg = Image.open(next_path)
        except FileNotFoundError:
            next_bg = self.bg_template

        self.current_page = next_bg.copy().convert("RGBA")
        self.cursor_x = self.cfg.margin_left + random.randint(-2, 2)
        self.cursor_y = self.cfg.margin_top + random.randint(-2, 2)

    def move_to_next_line(self):
        self.cursor_y += self.cfg.line_height
        self.cursor_x = self.cfg.margin_left + random.randint(-1, 2)
        if self.check_page_overflow():
            self.create_new_page()

    def ensure_page_has_room(self):
        if self.check_page_overflow():
            self.create_new_page()

    def render_char_at_cursor(
        self, ch: str, color: Tuple[int, int, int]
    ) -> None:
        fatigue_rot = min(2.0, self.current_page_idx * 0.4)

        char_img = self.glyph_mgr.prepare_char(
            ord(ch),
            color,
            fatigue_rot=fatigue_rot,
            opacity_factor=self.current_pressure,
        )
        if char_img is None:
            return

        x_jitter = random.randint(
            -self.cfg.random_x_offset, self.cfg.random_x_offset
        )
        y_jitter = random.randint(
            -self.cfg.random_y_offset, self.cfg.random_y_offset
        )
        paste_x = self.cursor_x + x_jitter
        paste_y = max(self.cfg.margin_top, self.cursor_y + y_jitter)

        if ch in ("=", "-", "+"):
            paste_y = self.cursor_y + (self.cfg.line_height - char_img.height) // 2
        elif ch == ":":
            paste_y = self.cursor_y + int(self.cfg.line_height * 0.28)

        self.current_page.paste(char_img, (paste_x, paste_y), char_img)
        
        spacing_jitter = random.randint(
            -self.cfg.random_spacing, self.cfg.random_spacing
        )
        step_x = char_img.width + self.cfg.char_spacing_offset + spacing_jitter
        self.cursor_x += max(1, step_x)

    def render_remaining_text(
        self, text_chunk: str, force_color: Optional[Tuple[int, int, int]] = None
    ):
        for ch in text_chunk:
            w = self.glyph_mgr.char_pixel_width(ch)
            if (
                self.check_line_overflow(w)
                and self.cursor_x != self.cfg.margin_left
            ):
                self.move_to_next_line()

            color = (
                force_color
                if force_color is not None
                else self.next_char_color(ch)
            )
            self.render_char_at_cursor(ch, color)

    def render_word_with_wrapping(
        self, word: str, force_color: Optional[Tuple[int, int, int]] = None
    ):
        self.word_counter += 1
        if self.word_counter % random.randint(4, 8) == 0:
            self.current_pressure = random.uniform(0.85, 1.0)

        word_width = self.glyph_mgr.measure_word_width(word)
        if (
            self.check_line_overflow(word_width)
            and self.cursor_x != self.cfg.margin_left
        ):
            self.move_to_next_line()

        self.render_remaining_text(word, force_color)

    def render_whitespace_run(self, run: str, suppress: bool) -> bool:
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
                self.move_to_next_line()
                suppress = True
                continue

            self.cursor_x += w
        return suppress

    def render_centred_line(self, line: str):
        self.ensure_page_has_room()
        line_width = self.glyph_mgr.measure_line_width(line)

        if line_width <= self.printable_width:
            centre_x = (
                self.cfg.margin_left + (self.printable_width - line_width) // 2
            )
            self.cursor_x = max(self.cfg.margin_left, centre_x)
            self.render_remaining_text(
                line, force_color=self.cfg.quote_ink_color
            )
            self.move_to_next_line()
        else:
            self.cursor_x = self.cfg.margin_left
            suppress = False
            for tok_type, tok_val in tokenise_line(line):
                if tok_type == "space":
                    suppress = self.render_whitespace_run(tok_val, suppress)
                else:
                    self.render_word_with_wrapping(
                        tok_val, force_color=self.cfg.quote_ink_color
                    )
                    suppress = False
            self.move_to_next_line()

    def process_text(self, text: str):
        for line in text.split("\n"):
            self.ensure_page_has_room()

            if line == "":
                self.cursor_y += self.cfg.line_height
                self.cursor_x = self.cfg.margin_left
                if self.check_page_overflow():
                    self.create_new_page()
                continue

            stripped = line.strip()

            if (
                stripped.startswith("||")
                and stripped.endswith("||")
                and len(stripped) >= 4
            ):
                self.render_centred_line(stripped[2:-2])
                continue

            if line.startswith("$"):
                tokens = tokenise_line(line[1:])
                if tokens:
                    first_token_type, first_token_val = tokens[0]
                    self.cursor_x = self.cfg.outdent_margin_left
                    self.render_remaining_text(first_token_val)
                    
                    self.cursor_x = max(self.cursor_x, self.cfg.margin_left)
                    tokens = tokens[1:]
                    
                    if tokens and tokens[0][0] == "space":
                        tokens = tokens[1:]
                        
                    suppress = False
                    for tok_type, tok_val in tokens:
                        if tok_type == "space":
                            suppress = self.render_whitespace_run(tok_val, suppress)
                        else:
                            self.render_word_with_wrapping(tok_val)
                            suppress = False

                    self.move_to_next_line()
                    continue

            self.cursor_x = self.cfg.margin_left
            suppress = False

            for tok_type, tok_val in tokenise_line(line):
                if tok_type == "space":
                    suppress = self.render_whitespace_run(tok_val, suppress)
                else:
                    self.render_word_with_wrapping(tok_val)
                    suppress = False

            self.move_to_next_line()

        self.pages.append(self.current_page)


# ══════════════════════════════════════════════════════════════════════════
#  4. HELPER FUNCTIONS & MAIN DRIVER
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


def main():
    input_filename = sys.argv[1] if len(sys.argv) > 1 else "test.txt"

    try:
        with open(input_filename, "r") as txt:
            text = txt.read()
    except FileNotFoundError:
        print(f"Could not find the file: {input_filename}")
        sys.exit(1)

    config = Config()
    glyph_mgr = GlyphManager(config)
    renderer = DocumentRenderer(config, glyph_mgr)

    renderer.process_text(text)

    # Convert all RGBA pages to RGB for clean PDF output
    rgb_pages = [page.convert("RGB") for page in renderer.pages]

    base_name = os.path.splitext(input_filename)[0]
    out_pdf_path = f"{base_name}_output.pdf"

    if rgb_pages:
        # Sequential multi-page PDF generation
        rgb_pages[0].save(
            out_pdf_path,
            save_all=True,
            append_images=rgb_pages[1:],
            resolution=100.0,
        )
        print(f"Successfully generated {len(rgb_pages)} page(s) PDF → {out_pdf_path}")


if __name__ == "__main__":
    main()