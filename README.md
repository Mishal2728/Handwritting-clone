# ✍️ Handwriting Studio

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-black.svg)](https://palletsprojects.com/p/flask/)
[![Pillow](https://img.shields.io/badge/Imaging-Pillow-green.svg)](https://python-pillow.org/)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

> A studio-grade, full-stack application that transforms plain digital text into authentic, organic human handwriting rendered onto realistic ruled assignment and notebook papers.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
  - [macOS 1-Click Launcher (start.command)](#1-macos-1-click-launcher-recommended)
  - [Manual Terminal Launch](#2-manual-terminal-launch)
  - [CLI Mode (Standalone Python Scripts)](#3-cli-mode-headless-batch-rendering)
- [Syntax Formatting Rules](#-syntax-formatting-rules)
- [Handwriting Realism Engine](#-handwriting-realism-engine)
- [Design & UI Architecture](#-design--ui-architecture)
- [REST API Endpoints](#-rest-api-endpoints)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Project Directory Structure](#-project-directory-structure)
- [Configuration Reference](#-configuration-reference)
- [Contributing & License](#-contributing--license)

---

## 🌟 Overview

**Handwriting Studio** bridges digital text input with realistic analog pen-on-paper aesthetics. Whether preparing university assignment submissions, revision study sheets, customized letters, or realistic exam answer scripts, this studio generates multi-page documents that accurately replicate natural human handwriting dynamics.

Unlike generic handwriting fonts that repeat identical glyphs mechanically, Handwriting Studio uses a glyph-variation engine that dynamically jitters angle, line spacing, stroke pressure, ink absorption, and human hand fatigue across multiple pages.

---

## ✨ Key Features

- **🎨 Modern Drafting Desk Interface**:
  - Dual-pane layout separating the writing slate from the live paper canvas.
  - Studio Dark (Obsidian) and Warm Parchment (Light) themes.
  - Dynamic line-number gutter synchronized with typing.
  - Drag-and-drop `.txt` file loading directly onto the editor.
  - Live metrics: character count, word count, line count, and estimated page count.

- **🖋️ Realistic Pen Physics & Imperfections**:
  - **Glyph Randomization**: Multiple authentic handwriting variations per character.
  - **Micro-Rotation**: Human wrist slant jitter (`0.0° – 3.5°`).
  - **Margin Fluctuation**: Human left-margin imperfections (`0px – 28px`).
  - **Ink Pressure Simulation**: Subtle flow fading and rejuvenation mimicking real fountain and gel pens.
  - **Multi-Page Fatigue Drift**: Progressive handwriting relaxation as the document grows.
  - **Unicode Auto-Normalization**: Automatic conversion of smart quotes, em-dashes, and non-breaking spaces.

- **📄 Authentic Ruled Paper Templates**:
  - 4 high-resolution ruled exercise book paper backgrounds (`bg1.png` – `bg4.png`).
  - Automatic paper randomization across multi-page documents to simulate real notebook spreads.
  - Manual selection option for consistent paper style across all pages.

- **🎨 Curated Ink Reservoirs**:
  - Quick swatches: Iron Gall Black (`#0f0f14`), Pilot Navy (`#1a365d`), Royal Ballpoint Blue (`#194bb4`), Sepia (`#2b1810`), and Exam Vermilion (`#dc2626`).
  - Integrated custom RGB/Hex color picker for any ink shade.

- **📦 Multi-Format Production Export**:
  - **Download PDF**: Single, multi-page, high-resolution document ready for submission or printing.
  - **Download ZIP**: Compressed archive of every individual page in PNG format.
  - **Download PNG**: Direct export of the active page view.
  - **Fullscreen Lightbox**: Inspect fine ink details up to 250% zoom.

---

## 🚀 Quick Start

### 1. macOS 1-Click Launcher (Recommended)

Simply double-click the **`start.command`** executable file in Finder.

- Automatically detects Python 3.
- Checks and auto-installs missing dependencies (`Flask`, `Pillow`).
- Avoids macOS AirPlay port conflicts by binding to an available port (default `5050`).
- Launches the web server and automatically opens your default browser at `http://localhost:5050`.
- Cleanly stops when you press <kbd>Ctrl</kbd> + <kbd>C</kbd> in the terminal window.

### 2. Manual Terminal Launch

Clone the repository and install the dependencies:

```bash
# Clone the repository
git clone https://github.com/Mishal2728/Handwritting-clone.git
cd Handwritting-clone

# Install dependencies
pip install -r requirements.txt

# Run the web application
python3 app.py
```

Open your browser and navigate to:
```
http://localhost:5050
```

### 3. CLI Mode (Headless Batch Rendering)

You can also run the core engine directly from the terminal without starting the web server:

```bash
# Generate multi-page PDF directly from a text file:
python3 texttopdf.py test.txt

# Generate individual PNG pages directly from a text file:
python3 texttoimg.py test.txt
```

---

## 📝 Syntax Formatting Rules

Handwriting Studio uses intuitive, lightweight formatting markup:

| Markup Syntax | Visual Result | Description |
|---|---|---|
| `\|\|SECTION - A\|\|` | Centered Heading | Automatically centers the heading horizontally and writes it using the secondary/highlight ink color. |
| `$1) Explain layers:` | Outdented Margin | Shifts the question number into the notebook's left margin, replicating student exam answer scripts. |
| `\|Key Concept\|` | Highlight Ink | Switches the enclosed phrase to the highlight ink color (e.g., Royal Blue or Red) while keeping body text in base ink. |
| Blank Line | Next Ruled Line | Advances down by one ruled notebook line. |
| Automatic Overflow | New Notebook Sheet | Automatically starts a new page when text reaches the bottom margin. |

### Example Input Document

```text
Name:|Mishal Ahamed|
Reg no:|261MCAN0135|
Subject:|Software Project Management|
Date:|22.11.2026|

||SECTION - A||

$1) a) |Reliability and Quality|
$2) b) |Iterative Process Model|

||SECTION - B||

$3) Explain why Software Engineering is a layered technology:
|Software engineering comprises four distinct layers working together to deliver high-quality systems:|

Four Layers:
$I. Quality Focus
|Quality is the bedrock upon which all organizational practices rest.|

$II. Process
|Provides the framework and milestones for structured delivery.|

$III. Methods
|Encompasses the technical design, architectural patterns, and testing.|

$IV. Tools
|Provides automated and semi-automated support across all stages.|
```

---

## 🎛️ Handwriting Realism Engine

The rendering pipeline in `generator.py` executes these steps for every word:

```
Input Text
    │
    ▼
[Text Normalizer] ── Converts smart quotes (“ ”), en-dashes (–), non-breaking spaces
    │
    ▼
[Line Tokenizer] ── Identifies Heading (||..||), Question ($), and Words/Spaces
    │
    ▼
[Word Wrap Engine] ── Calculates character widths; breaks lines without splitting words
    │
    ▼
[Glyph Loader] ── Selects character variants from font/ directory
    │
    ├── Micro-Scale Jitter (0.97x – 1.03x)
    ├── Slant Rotation (BICUBIC rotation per character)
    ├── Color Noise (±5 RGB value fluctuation for ink depth)
    └── Pressure Variation (Simulates ink flow & fading)
    │
    ▼
[Paper Compositor] ── Pastes onto ruled background (bg1.png – bg4.png)
    │
    ▼
Output: Multi-Page PDF / PNGs / ZIP
```

---

## 🎨 Design & UI Architecture

The frontend is built with clean HTML5, modern CSS3 tokens, and native JavaScript:

- **Stationery Desk Aesthetics**: Modeled after physical drafting desks rather than generic SaaS cards.
- **Collapsible Inspector**: Toggle the style drawer via the toolbar or shortcut (`⌥S`) to expand editing space.
- **Floating Lens Dock**: Zoom controls (`−`, `100%`, `+`, `↺ Fit`, `⛶ Fullscreen`) floating smoothly over the canvas.
- **Thumbnail Filmstrip**: Interactive drawer displaying rendered sheets with active focus indicators.
- **Accessible Typography**: Styled with `Plus Jakarta Sans` for UI chrome and `JetBrains Mono` for drafting.
- **Zero External Icon Fonts**: Crisp, inline vector SVGs that work 100% offline without CDN latency.

---

## 🌐 REST API Endpoints

The Flask application exposes a clean REST API:

| Endpoint | Method | Payload / Query | Description |
|---|---|---|---|
| `/` | `GET` | — | Serves the single-page application. |
| `/api/sample` | `GET` | — | Returns sample text from `test.txt`. |
| `/api/upload` | `POST` | `multipart/form-data` (`file`) | Uploads and parses a `.txt` document. |
| `/api/render` | `POST` | JSON `{ text, config, preview_only }` | Renders the text and returns page URLs and metadata. |
| `/api/page/<id>/<num>` | `GET` | `?thumb=1` (optional) | Streams high-resolution or thumbnail JPEG of a page. |
| `/api/download/pdf/<id>` | `GET` | `?name=filename.pdf` | Streams the compiled multi-page PDF download. |
| `/api/download/zip/<id>` | `GET` | `?name=filename.zip` | Streams a ZIP archive containing all PNG pages. |
| `/api/download/page/<id>/<num>` | `GET` | — | Streams an individual page as a PNG file. |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>⌘</kbd> + <kbd>Enter</kbd> / <kbd>Ctrl</kbd> + <kbd>Enter</kbd> | **Generate All Pages** |
| <kbd>⌘</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd> | **Fast Preview** (Page 1) |
| <kbd>⌘</kbd> + <kbd>S</kbd> / <kbd>Ctrl</kbd> + <kbd>S</kbd> | **Download PDF** |
| <kbd>⌘</kbd> + <kbd>K</kbd> / <kbd>Ctrl</kbd> + <kbd>K</kbd> | **Open Syntax Guide** |
| <kbd>⌥</kbd> + <kbd>S</kbd> | **Toggle Style Drawer** |
| <kbd>←</kbd> / <kbd>→</kbd> | **Previous / Next Page** |
| <kbd>Tab</kbd> | **Indent 4 Spaces in Editor** |
| <kbd>Esc</kbd> | **Close Modals & Lightbox** |

---

## 📁 Project Directory Structure

```
Handwritting-clone/
├── .gitignore              # Ignores __pycache__, .DS_Store, and temporary files
├── README.md               # Complete project documentation
├── requirements.txt        # Python dependency manifest
├── start.command           # macOS 1-click executable launcher script
├── app.py                  # Flask web server & REST API service
├── generator.py            # Core handwriting rendering & export engine
├── texttoimg.py            # Standalone CLI renderer for PNG output
├── texttopdf.py            # Standalone CLI renderer for PDF output
├── test.txt                # Sample assignment and examination text
├── font/                   # Character glyph database & paper backgrounds
│   ├── 32.png ... 125.png  # Individual ASCII character stroke glyphs
│   ├── bg1.png – bg4.png   # High-resolution ruled exercise book paper templates
│   └── underline.png       # Formatting underline asset
└── templates/
    └── index.html          # Modern studio single-page application
```

---

## ⚙️ Configuration Reference

The `HandwritingConfig` class in `generator.py` supports these parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `margin_left` | `int` | `230` | Left notebook margin (in pixels). |
| `margin_right` | `int` | `40` | Right margin buffer to prevent edge clipping. |
| `margin_top` | `int` | `60` | Top header margin. |
| `margin_bottom` | `int` | `60` | Bottom margin before creating a new page. |
| `line_height` | `int` | `110` | Spacing between ruled notebook lines. |
| `outdent_margin_left` | `int` | `180` | Hanging margin start position for question numbers (`$`). |
| `random_line_indent` | `int` | `14` | Uneven left-margin fluctuation range. |
| `font_scale` | `float` | `0.70` | Overall font size scale (`0.55 – 0.95`). |
| `char_spacing_offset` | `int` | `-2` | Letter spacing offset. |
| `random_rotation` | `float` | `1.6` | Maximum random character tilt angle (in degrees). |
| `default_ink_color` | `tuple` | `(15, 15, 20)` | RGB base ink color (Iron Gall Black). |
| `quote_ink_color` | `tuple` | `(25, 75, 180)` | RGB highlight ink color (Royal Blue). |
| `background_choice` | `int` | `0` | Paper background (`0` = auto mix, `1..4` = specific paper). |
| `enable_pressure` | `bool` | `True` | Simulates pen ink fading and flow recovery. |
| `enable_fatigue` | `bool` | `True` | Gradually increases tilt drift on later pages. |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

Developed with ❤️ by [Mishal2728](https://github.com/Mishal2728)
