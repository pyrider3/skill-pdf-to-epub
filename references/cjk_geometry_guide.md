# CJK & Geometry-Based PDF to EPUB Conversion Guide

This guide details the methodology, geometric heuristics, and text-cleaning algorithms used to transform complex, multi-page PDFs (such as LaTeX, InDesign, or Word publications) into publishing-grade EPUB 3 / EPUB 2 digital books.

---

## 1. The Core Challenge: Coordinate Space vs. Flowable Semantics

A PDF is essentially a graphical canvas of positioned glyphs, lines, and raster images. It has **no concept of paragraphs, headings, footnotes, or reflowable text**.
When naive tools (Pandoc, Calibre `ebook-convert`, unguided `pdftotext`) attempt conversion, they create severe reading defects:
1. **Accidental Line Breaks**: Every visual line in the PDF becomes a hard `<p>` or `<br/>`, shattering sentences into fragments.
2. **Orphan Leading Punctuation**: Punctuation marks (`，`, `。`, `、`, `”`, `）`, `》`) land at the start of new lines/paragraphs.
3. **Stray Running Headers/Footers**: Chapter titles and page numbers repeated at the top/bottom of every PDF page pollute the body text.
4. **Footnote Entanglement**: When a paragraph spans across a page boundary, footnotes printed at the bottom of the first page get inserted directly into the middle of the sentence.
5. **CJK Justification Spaces**: Justification spacing in PDFs injects spaces between Chinese/Japanese characters (`建 模 之 后` instead of `建模之后`).
6. **Lost Visual Elements**: Photos, charts, code blocks, theorem boxes, and math formulas lose their formatting or are dropped entirely.

---

## 2. Extraction Pipeline: The Four Pillars

### Pillar 1: Image & Asset Extraction
* **Cover Page Rendering**:
  ```bash
  pdftoppm -png -r 300 -f 1 -l 1 input.pdf OEBPS/Images/cover_tmp
  ```
  Renders page 1 at 300 DPI for a razor-sharp cover image.
* **Lossless Image Extraction**:
  ```bash
  pdfimages -png input.pdf OEBPS/Images/img
  ```
  Dumps all original raster assets (photos, diagrams) without re-compression or resolution loss.

### Pillar 2: Coordinate Extraction (`pdftotext -bbox-layout`)
Instead of plain text, extract word bounding boxes:
```bash
pdftotext -bbox-layout input.pdf bbox_layout.xml
```
* **Performance**: Ultra-fast (0.1s for 100 pages).
* **Metadata provided per word**: `xMin`, `xMax`, `yMin`, `yMax`, font height (`yMax - yMin`), text.

---

## 3. Geometric Classification Heuristics

On a standard PDF page (e.g. 360pt × 576pt):

| Element Type | Geometric Criterion | Example Values |
| :--- | :--- | :--- |
| **Running Header** | `yMin < Y_HEADER_THRESHOLD` | `yMin < 45.0 pt` |
| **Running Footer (Page #)** | `yMin > Y_FOOTER_THRESHOLD` | `yMin > 525.0 pt` |
| **Body Text Area** | `45.0 pt <= yMin <= 525.0 pt` | Text lines |
| **Paragraph Start** | First line has indentation `xMin >= X_INDENT_THRESHOLD` | `xMin = 55.9 pt` (vs margin `36.0 pt`) |
| **Paragraph Continuation**| Line starts at standard left margin | `xMin = 36.0 pt` |
| **Footnotes** | `yMin > Y_FN_ZONE` AND `avg_height <= 8.5 pt` AND starts with `^[1-9][0-9]?\s+` | Font is 70-80% of body size |
| **Footnote Ref in Body** | Word text is digit `1..20` AND `height <= 7.5 pt` | Superscript reference |

### Identifying Page Boundary Continuations
When a paragraph continues from Page $N$ to Page $N+1$:
1. The last line of Page $N$ has `xMin = 36.0 pt` (body margin).
2. Any footnotes on Page $N$ are filtered out and stored in the chapter footnote buffer.
3. The first line of Page $N+1$ has `xMin = 36.0 pt` (no indent).
4. **Action**: Join the first line of Page $N+1$ directly to the pending paragraph of Page $N$ using `join_cjk()`.

---

## 4. Text Cleaning & Unwrapping Algorithms

### CJK Justification Space Stripper
```python
def clean_cjk_spaces(text):
    cjk = r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'
    prev = None
    while prev != text:
        prev = text
        text = re.sub(f'({cjk}) +({cjk})', r'\1\2', text)
    # Remove space after opening punctuation
    text = re.sub(r'([“‘（《【]) +', r'\1', text)
    # Remove space before closing punctuation
    text = re.sub(r' +([”’）》】])', r'\1', text)
    return text.strip()
```

### Semantic Line Joiner (`join_cjk`)
```python
def join_cjk(s1, s2):
    if not s1: return s2
    if not s2: return s1
    # Handle stray half-width commas
    if s2.startswith(','):
        return s1 + '，' + s2[1:].lstrip()
    # If boundary is between English words or numbers, preserve space
    if re.search(r'[A-Za-z0-9]$', s1) and re.match(r'^[A-Za-z0-9]', s2):
        return s1 + ' ' + s2
    # CJK boundary: join seamlessly with NO space
    return s1 + s2
```

---

## 5. Semantic Element Design Patterns

### Callouts & Theorems
```html
<div class="theorem-box">
    <div class="theorem-title">公理 1</div>
    <p>在自由状态下，女人绝大多数决策都是基于感觉...</p>
</div>
```

### Code Blocks
```html
<pre class="code-block"><code>/*********************
* Project: Sirius
* Author: Sinya
*********************/</code></pre>
```

### Math Display
```html
<div class="math-display">
    <span class="math-symbol">∑</span><sub class="math-sub">i=0</sub><sup class="math-sup">n</sup> (p<sub>i</sub> v<sub>i</sub> − c<sub>i</sub>)
</div>
```

### Bidirectional Footnotes
* In Body:
  ```html
  <p>中国实行铁绿帽法<sup><a href="#fn-ch2-1" id="ref-ch2-1">[1]</a></sup>...</p>
  ```
* In Footnotes Section:
  ```html
  <section class="footnote-section" epub:type="footnotes">
      <div class="footnote-heading">注释</div>
      <div class="footnote-item" id="fn-ch2-1">
          <a href="#ref-ch2-1" class="footnote-backlink">[1]</a>
          <span class="footnote-text">指丈夫有责任供养妻子婚内出轨所生子女的法律。</span>
      </div>
  </section>
  ```

---

## 6. EPUB Validation Quality Checklist

A build is only complete when it passes all 6 gates:
1. `mimetype` is uncompressed `ZIP_STORED` and the first entry in ZIP.
2. Every XML/XHTML file parses cleanly with `xml.etree.ElementTree.fromstring`.
3. Every file in `content.opf` manifest exists in ZIP.
4. Every `<img src="...">` resolves to an existing file in `Images/`.
5. **Zero paragraphs start with orphan punctuation (`^[，。、；：？！’”’）》』]`)**.
6. Every footnote `href` matches a corresponding `id` target.
