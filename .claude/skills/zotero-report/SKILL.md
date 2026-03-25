---
name: zotero-report
description: >
  Generate comprehensive research reports from Zotero collections with Obsidian integration.
  Supports 3 modes: (1) existing collection, (2) collection + arXiv extension,
  (3) topic search from scratch. Creates per-paper Obsidian summary notes.
  Export to MD/DOCX/PDF/HWPX.
  Use when users want literature reviews, research trend analysis, or paper summaries.
allowed-tools: Read,Bash,Write
---

# Zotero Report Skill

Generate comprehensive research reports from Zotero collections.

## Prerequisites

- Configuration file at `config/config.json` with Zotero and Obsidian settings
- Environment variable `ZOTERO_API_KEY`

## Step 0: Mode + Format Detection

Detect mode from user request:
- "이 컬렉션 보고서 만들어줘" → Mode 1 (collection)
- "관련 논문 더 찾아서 보고서" → Mode 2 (extend)
- "X 주제로 논문 찾아서 보고서" → Mode 3 (topic)

Detect format:
- "PDF로", "워드로", "hwpx로" → that format
- Default: Markdown

## Mode 1: Collection-Only

### Phase 1 - Data Collection
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/generate_report.py \
  --mode collection --collection "COLLECTION_NAME"
```

For deeper analysis with full text:
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/generate_report.py \
  --mode collection --collection "COLLECTION_NAME" \
  --include-full-text --max-chars-per-paper 10000
```

### Phase 2 - Analysis
Read the JSON output. For each paper:
- Generate 3-5 line summary from abstract + pdf_text_preview
- Identify cross-cutting themes, methodological patterns, research gaps

### Phase 3 - Report Writing
Use `templates/report_template.md` as guide. Write Markdown report and save as `{collection_name}-report.md`.

### Phase 4 - Obsidian Notes
For each paper in the JSON, create an Obsidian summary note:
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/obsidian-summarize/scripts/create_summary.py \
  --arxiv-id "ID" --title "TITLE" --authors "AUTHORS" \
  --abstract "ABSTRACT" --zotero-key "KEY" \
  --subfolder "COLLECTION_NAME" \
  --summary "GENERATED_SUMMARY" --key-findings "F1|F2|F3" \
  --force
```

### Phase 5 - Export (if requested)
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/export_report.py \
  --input {name}-report.md --format {docx|pdf|hwpx} \
  --output {name}-report.{ext}
```

## Mode 2: Collection + Extension

### Phase 1a - Collect existing data + search queries
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/generate_report.py \
  --mode extend --collection "COLLECTION_NAME"
```

### Phase 1b - Search arXiv using suggested queries
Read `suggested_search_queries` from JSON. For each query:
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "QUERY" --max-results 10 --output json
```

### Phase 1c - Add relevant papers to Zotero
Review results. For papers not already in the collection:
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "ID" --title "TITLE" --authors "AUTHORS" \
  --abstract "ABSTRACT" --published "DATE" \
  --collection "COLLECTION_NAME"
```

### Phase 1d - Re-collect updated collection
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/generate_report.py \
  --mode collection --collection "COLLECTION_NAME"
```

### Phase 2-5: Same as Mode 1

## Mode 3: Topic Search from Scratch

### Phase 1a - Search arXiv
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "TOPIC_KEYWORDS" --max-results 20 --output json --sort-by relevance
```

### Phase 1b - Add to Zotero
For each paper in search results:
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "ID" --title "TITLE" --authors "AUTHORS" \
  --abstract "ABSTRACT" --published "DATE" \
  --collection "TOPIC_AS_COLLECTION_NAME"
```

### Phase 1c - Collect data
```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 \
  .claude/skills/zotero-report/scripts/generate_report.py \
  --mode collection --collection "TOPIC_AS_COLLECTION_NAME"
```

### Phase 2-5: Same as Mode 1

## Error Handling

- **Collection not found**: Ask user to verify collection name
- **arXiv search 0 results**: Suggest different keywords
- **Zotero add fails**: Skip paper, continue, report failures
- **PDF extraction fails**: Use abstract only for summary
- **Export fails**: MD file is already saved, check tool installation

## Obsidian Note Rules

- Subfolder name = Zotero collection name (exact match)
- Use `--force` to overwrite without prompt
- Papers without arxiv_id: use zotero key as identifier
- Papers without abstract: use pdf_text_preview

## Known Limitations

- Linked file attachments: local path must be accessible
- Scanned PDFs (image-only): OCR not supported, use abstract
- HWPX export: uses `--no-preprocess` (no government formatting)
- non-arXiv papers: zotero_key used as identifier

## Agent Orchestration (OMC)

For large collections (50+ papers):
```
/team 2:executor "batch 1: papers 1-25" "batch 2: papers 26-50"
Then use analyst agent for synthesis.
```
