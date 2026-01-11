---
name: zotero-add
description: Add academic papers to Zotero library. Use when users want to save papers to Zotero, create collections, or organize their research library. Handles PDF downloads and metadata.
allowed-tools: Read,Bash,Write
---

# Zotero Paper Management Skill

Add papers to Zotero with full metadata and PDF attachments.

## Prerequisites

1. Configuration file at `config/config.json` with Zotero settings
2. Environment variable `ZOTERO_API_KEY` or in `.env` file
3. Get API key from: https://www.zotero.org/settings/keys

## Usage

Add a paper to Zotero:

```bash
cd /Users/varde/code/arxiv-zotero-obsidian && python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "2401.12345" \
  --title "Paper Title" \
  --authors "Author One,Author Two" \
  --abstract "Paper abstract..." \
  --published "2024-01-15" \
  --collection "Collection Name"
```

## Available Options

| Option | Description | Required |
|--------|-------------|----------|
| `--arxiv-id` | arXiv paper ID | Yes |
| `--title` | Paper title | Yes |
| `--authors` | Comma-separated author names | Yes |
| `--abstract` | Paper abstract | No |
| `--published` | Publication date | No |
| `--collection` | Zotero collection name | No |
| `--tags` | Comma-separated tags | No |
| `--skip-pdf` | Skip PDF download | No |
| `--doi` | Paper DOI | No |

## Examples

```bash
# Basic add with PDF
python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "1706.03762" \
  --title "Attention Is All You Need" \
  --authors "Ashish Vaswani,Noam Shazeer,Niki Parmar" \
  --published "2017-06-12" \
  --collection "Transformers"

# Add with tags, skip PDF
python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "2401.12345" \
  --title "Example Paper" \
  --authors "John Doe" \
  --tags "machine-learning,nlp" \
  --skip-pdf
```

## Workflow

1. Script creates or finds the specified collection
2. Creates a journalArticle item with metadata
3. Downloads PDF from arXiv (unless --skip-pdf)
4. Attaches PDF to the item
5. Returns item key for reference

## Output

Returns JSON with:
- `item_key`: Zotero item identifier
- `collection_key`: Collection identifier (if used)
- `pdf_attached`: Boolean indicating PDF upload success

## Integration with arxiv-search

After searching with arxiv-search skill, use the arxiv_id from results:

```bash
# From search result [1] with arxiv_id 2401.12345
python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "2401.12345" \
  --title "..." --authors "..."
```

## Troubleshooting

- **API Key Error**: Check ZOTERO_API_KEY in .env or environment
- **Library ID Error**: Verify library_id in config/config.json
- **PDF Upload Failed**: Check internet connection, retry with --skip-pdf
