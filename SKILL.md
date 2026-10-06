---
name: pdf-to-epub
description: >-
  Expert system for converting complex PDF documents (books, essays, academic papers, reports, LaTeX/InDesign/Word publications) into publishing-grade, responsive EPUB 3 / EPUB 2 digital books. Eliminates broken sentences, orphan leading punctuation, stray running headers/footers, entangled footnotes, and CJK justification artifacts. Formats theorem boxes, math formulas, code blocks, and losslessly embeds high-resolution images.
---

# PDF to EPUB Master Skill

This skill provides an end-to-end, battle-tested procedure to convert complex PDF documents into publishing-grade, reflowable EPUB 3 / EPUB 2 books with clean typography, dark-mode responsiveness, and complete structural integrity.

---

## When to Use This Skill

Activate this skill whenever:
* The user asks to convert a PDF into EPUB format (e.g. "转成EPUB", "把这个转成EPUB", "PDF转EPUB").
* The user requests high reading quality, dark mode support, and no broken sentences or orphan punctuation.
* The document contains CJK (Chinese, Japanese, Korean) text, LaTeX layouts, footnotes, embedded photos/figures, theorems, or math formulas.

---

## Core Pipeline Architecture

```
[ Input PDF ]
      │
      ├─► pdftoppm -r 300 (Cover rendering) ───────────► OEBPS/Images/cover.png
      ├─► pdfimages -png (Lossless image extraction) ──► OEBPS/Images/fig_*.png
      └─► pdftotext -bbox-layout (0.1s coordinate XML) ──► Word Bounding Boxes
                                                                │
                                   ┌────────────────────────────┘
                                   ▼
             [ Geometric Segmentation & Classification ]
             • yMin < 45pt  ──► Running Headers (Filter out)
             • yMin > 525pt ──► Running Footers / Page # (Filter out)
             • yMin > 400pt & h <= 8.5pt ──► Footnote Definitions
             • h <= 7.5pt in body ───────► Superscript Footnote Ref
             • xMin >= 50pt ─────────────► New Paragraph Indentation
             • xMin < 50pt  ─────────────► Continuation of Sentence
                                   │
                                   ▼
                [ CJK Spacing & Sentence Unwrapper ]
             • Strip justification spaces between CJK chars
             • Join lines seamlessly across pages (zero mid-sentence breaks)
             • Assert 0 paragraphs start with orphan punctuation
                                   │
                                   ▼
              [ Semantic XHTML & CSS Assembly (Dual-Mode) ]
             • Callout & Theorem boxes (.theorem-box)
             • Code blocks with syntax styling (.code-block)
             • Math expressions with sub/sup formatting (.math-display)
             • Bidirectional interactive footnotes (<sup><a href="#fn-*">)
             • Dual Navigation: EPUB 3 nav.xhtml + EPUB 2 toc.ncx
                                   │
                                   ▼
                       [ ZIP Packager & Verification ]
             • Uncompressed mimetype as 1st file (ZIP_STORED)
             • Automated verification suite (XML, Manifest, 0-Punct, Links)
```

---

## Detailed Step-by-Step Procedure

### Step 1: Workspace & Asset Extraction

1. Create a dedicated workspace directory:
   ```bash
   mkdir -p epub_workspace/{epub_build/META-INF,epub_build/OEBPS/{Text,Images,Styles},extracted_assets}
   ```
2. Render high-resolution cover (Page 1 at 300 DPI):
   ```bash
   pdftoppm -png -r 300 -f 1 -l 1 input.pdf epub_workspace/epub_build/OEBPS/Images/cover_tmp
   mv epub_workspace/epub_build/OEBPS/Images/cover_tmp-*.png epub_workspace/epub_build/OEBPS/Images/cover.png
   ```
3. Extract all raw raster images losslessly:
   ```bash
   pdfimages -png input.pdf epub_workspace/extracted_assets/img
   ```
   Inspect extracted images and copy relevant figures into `OEBPS/Images/` with clear semantic names (`fig_1_1.png`, etc.).
4. Extract full-precision coordinate bounding boxes:
   ```bash
   pdftotext -bbox-layout input.pdf epub_workspace/bbox_layout.xml
   ```

---

### Step 2: Coordinate Analysis & Boundary Tuning

Examine `bbox_layout.xml` to determine exact page geometry (typically standard 5x8 inch book layout, e.g., 360pt × 576pt):
* **Header Zone**: Any line with `yMin < Y_HEADER` (usually `yMin < 45.0 pt`).
* **Footer Zone**: Any line with `yMin > Y_FOOTER` (usually `yMin > 525.0 pt`).
* **Footnote Zone**: Any line with `yMin > Y_FN_ZONE` (usually `yMin > 400.0 pt`) having font height `avg_h <= 8.5 pt` and matching `^[1-9][0-9]?\s+`.
* **Two-Column / Multi-Column Pages**: When a page has two columns (e.g. left col `x < 315 pt` and right col `x >= 315 pt`), **never sort purely by vertical `top` across the page**; that scrambles left and right columns into an unreadable mess! Process Column 1 top-to-bottom, then Column 2 top-to-bottom.
* **Horizontal Line Fragment Merging**: InDesign often cuts a single physical line into multiple `<text>` boxes with identical `top` (e.g. bolded words or justification runs). Always merge fragments on the same line horizontally before paragraph processing.
* **Indented Blocks / Lists**: In numbered lists (e.g. `1. `, `2. `) or blockquotes, all lines share the same indent `left >= indent`. Do not treat every indented line as a separate paragraph; only split on list item numbers or actual paragraph gaps!
* **Cross-Page Flow**: When a sentence crosses page boundaries, strip the bottom footnotes and headers, then join the top continuation line directly to the pending paragraph.

---

### Step 3: Text Cleaning & CJK Unwrapping

Use the following battle-tested Python functions and rules:

```python
import re

def clean_cjk_spaces(text):
    cjk = r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'
    prev = None
    while prev != text:
        prev = text
        text = re.sub(f'({cjk}) +({cjk})', r'\1\2', text)
    text = re.sub(r'([“‘（《【]) +', r'\1', text)
    text = re.sub(r' +([”’）》】])', r'\1', text)
    return text.strip()

def join_cjk(s1, s2):
    if not s1: return s2
    if not s2: return s1
    if s2.startswith(','):
        return s1 + '，' + s2[1:].lstrip()
    if s2.startswith('。') and s1.endswith('。'):
        return s1
    if re.search(r'[A-Za-z0-9]$', s1) and re.match(r'^[A-Za-z0-9]', s2):
        return s1 + ' ' + s2
    return s1 + s2
```

**Hard Sentence Unwrapping Rule**:
A line **MUST NOT** be treated as a new paragraph if the preceding line did not end with sentence-terminating punctuation (`[。！？……][”’』）]?$`), unless the next line is an explicit heading. Mid-sentence word breaks across lines (e.g. `蓝药` / `丸`, `有着雄性主` / `导意识`) must always be joined seamlessly.

**Quality Criterion (Must Pass)**:
Assert that no paragraph begins with orphan punctuation:
```python
LEADING_PUNCT = re.compile(r'^[，。、；：？！’”’）》』]')
assert not any(LEADING_PUNCT.match(p) for p in paragraphs)
```

---

### Step 4: Semantic Document Formatting

1. **Chapter Header**:
   ```html
   <div class="chapter-header">
       <div class="chapter-number">第一章</div>
       <h1 class="chapter-title">前言</h1>
   </div>
   ```
2. **Theorems / Axioms / Corollaries**:
   ```html
   <div class="theorem-box">
       <div class="theorem-title">公理 1</div>
       <p>在自由状态下，女人绝大多数决策都是基于感觉...</p>
   </div>
   ```
3. **Figures & Illustrations**:
   ```html
   <figure class="figure-container">
       <img src="../Images/fig_1_1.png" alt="图 1.1 说明" />
       <figcaption class="figure-caption">图 1.1: 说明文字</figcaption>
   </figure>
   ```
4. **Math Formulas**:
   ```html
   <div class="math-display">
       <span class="math-symbol">∑</span><sub class="math-sub">i=0</sub><sup class="math-sup">n</sup> p<sub>i</sub>
   </div>
   ```
5. **Bidirectional Footnotes**:
   * Reference in body:
     ```html
     <sup><a href="#fn-ch1-1" id="ref-ch1-1">[1]</a></sup>
     ```
   * Section at end of chapter:
     ```html
     <section class="footnote-section" epub:type="footnotes">
         <div class="footnote-heading">注释</div>
         <div class="footnote-item" id="fn-ch1-1">
             <a href="#ref-ch1-1" class="footnote-backlink">[1]</a>
             <span class="footnote-text">注释正文内容。</span>
         </div>
     </section>
     ```

---

### Step 5: Master Stylesheet & Navigation

1. Copy the master stylesheet from [resources/style.css](./resources/style.css) into `epub_build/OEBPS/Styles/style.css`.
2. Generate reader-facing Table of Contents in `OEBPS/Text/toc.xhtml`.
3. Generate EPUB 3 Navigation document in `OEBPS/nav.xhtml` (with `epub:type="toc"` and `epub:type="landmarks"`).
4. Generate EPUB 2 NCX in `OEBPS/toc.ncx` for full backward compatibility.
5. Generate `META-INF/container.xml` pointing to `OEBPS/content.opf`.
6. Generate `OEBPS/content.opf` declaring all items in `<manifest>` and reading order in `<spine toc="ncx">`.

---

### Step 6: Packaging & Automated Verification

1. Run the packaging script:
   ```bash
   python3 ~/.gemini/config/skills/pdf-to-epub/scripts/package_epub.py epub_build output.epub
   ```
   *Ensures `mimetype` is uncompressed `ZIP_STORED` and the first file in archive.*
2. Run the automated verification suite:
   ```bash
   python3 ~/.gemini/config/skills/pdf-to-epub/scripts/verify_epub.py output.epub
   ```
   *Verifies: 100% valid XML, all manifest files present, all image links resolve, 0 paragraphs start with invalid punctuation, all footnote links resolve.*

---

## Helper Scripts & References

* **[scripts/extract_assets.py](./scripts/extract_assets.py)**: Automated asset extraction (cover, images, bbox XML).
* **[scripts/package_epub.py](./scripts/package_epub.py)**: Compliant EPUB packager.
* **[scripts/verify_epub.py](./scripts/verify_epub.py)**: 6-gate verification suite.
* **[resources/style.css](./resources/style.css)**: Master EPUB CSS stylesheet with dark mode and CJK typography.
* **[references/cjk_geometry_guide.md](./references/cjk_geometry_guide.md)**: Deep dive on coordinate heuristics and CJK unwrapping algorithms.
