# arXiv Paper Extraction

arXiv abstract pages (`arxiv.org/abs/XXXX.XXXXX`) present a two-layer content problem for document conversion.

## The Problem

Jina Reader (and most text extractors) fetch the HTML abstract page, which contains:
- Title, authors, arXiv ID, submission dates
- Abstract text (usually 1-2 paragraphs)
- Metadata (subjects, DOI, citation tools)
- **Not the full paper content**

The actual paper content lives in the PDF at `arxiv.org/pdf/XXXX.XXXXX`.

## Extraction Strategy

### Step 1: Quick metadata via Jina

Use Jina to get the abstract and metadata for the document header:

```bash
curl -s "https://r.jina.ai/https://arxiv.org/abs/2407.18384" -H "Accept: text/plain" | head -50
```

### Step 2: Download PDF for full content

```bash
curl -sL -o /tmp/paper.pdf "https://arxiv.org/pdf/2407.18384"
```

### Step 3: Extract text with pymupdf

```python
import fitz
doc = fitz.open('/tmp/paper.pdf')
print(f'Total pages: {len(doc)}')

# Extract specific pages
for i in range(min(10, len(doc))):
    text = doc[i].get_text()
    print(f'\n--- Page {i+1} ---')
    print(text[:2000])
```

**Notes:**
- `fitz.open()` does **not** accept URLs directly — download first
- Mathematical notation comes through as LaTeX fragments or Unicode; review before including in prose
- Figures and equations may need manual description since they are not extracted as images
- **Batch extraction for long papers**: if `len(doc)` > 15, split into chunks (e.g., pages 0-19, then 20-end) to avoid terminal output limits. Use `doc[i].get_text()` per page and truncate per-page output (`[:1500]`) to keep context manageable

## Content Decisions for Long Documents

arXiv papers (especially books/monographs) are often 100-300+ pages. For Kami conversion:

| Source length | Approach |
|---|---|
| 10-20 pages (short paper) | Extract and translate full content |
| 20-40 pages (standard paper, dense) | **Distill into a condensed research guide**: extract key claims, tables, figures, and representative examples; omit methodological minutiae, exhaustive ablation tables, and reference lists. Target ~40-60% of original length. |
| 100+ pages (book/monograph) | Extract TOC, preface, and 1-2 representative chapters; summarize the rest |
| Survey/review papers | Extract section headings as a structured overview; include key theorems as callouts |

## Document Type Selection

- **Research paper** (≤30 pages, single narrative) → `long-doc` with full translation
- **Book/monograph** (100+ pages, multiple chapters) → `long-doc` as a **reader's guide / 导读版**: cover, TOC, chapter-by-chapter summaries, key theorems highlighted, full structure overview in the final chapter
- **Course notes / lecture notes** → `long-doc` with emphasis on pedagogical flow

## Example: Book-length arXiv document

For a 333-page book like arXiv:2407.18384 (*Mathematical Theory of Deep Learning*):

1. Extract TOC pages (usually pages 2-4 of the PDF)
2. Extract preface/introduction for the book's stated goals and audience
3. Extract 1-2 key chapters in depth (e.g., universal approximation, optimization theory)
4. For remaining chapters, create summary tables with chapter number, title, and 1-line description
5. Structure the Kami document as a **导读** (reader's guide) rather than a full translation

This respects the original work while making it accessible to readers who want to understand the book's scope before diving into the full PDF.
