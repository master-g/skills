# arXiv Paper Extraction

arXiv abstract pages (`arxiv.org/abs/XXXX.XXXXX`) present a two-layer content problem for document conversion.

## The Problem

An abstract-page extraction contains:

- Title, authors, arXiv ID, submission dates
- Abstract text (usually 1-2 paragraphs)
- Metadata (subjects, DOI, citation tools)
- **Not the full paper content**

The actual paper content lives in the PDF at `arxiv.org/pdf/XXXX.XXXXX`.

## Extraction Strategy

### Step 1: Metadata

Use the current permitted extraction tool for the document header. If Jina is available, for example:

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

# Preview only: this displays truncated excerpts, not complete extraction
for i in range(min(10, len(doc))):
    text = doc[i].get_text()
    print(f'\n--- Page {i+1} ---')
    print(text[:2000])
```

**Notes:**

- `fitz.open()` does **not** accept URLs directly — download first
- Mathematical notation comes through as LaTeX fragments or Unicode; review before including in prose
- Figures and equations may need manual description since they are not extracted as images
- For long papers, read the requested pages in batches and record coverage. Truncated output is only a preview; continue through the remaining text before claiming full coverage.

## Scope and document type

Follow the user's requested output: full conversion, selected sections, summary or reader's guide.
Page count helps estimate work; it does not authorize changing that output or dropping methods,
references or chapters. If a scope decision is necessary, explain it and wait for the user's answer.

- Full conversion: extract all requested pages and check figures, equations and text order. Respect the current environment's reproduction limits.
- Summary: read the material needed to support each summarized claim. State omitted or unread sections.
- Reader's guide: use the TOC and introduction to orient the reader, then read the selected chapters. Descriptions inferred from headings are coverage notes, not summaries of unread chapters.

Use the available Kami template suited to the agreed document, usually `long-doc` for papers
or guides. Label abridged output explicitly; never present excerpts or a guide as a full translation.
