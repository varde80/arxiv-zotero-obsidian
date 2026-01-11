# arXiv-Zotero-Obsidian AI Agent 구현 계획

## 개요
Claude Code 기반의 AI 에이전트를 Skills 아키텍처로 구현하여 학술 논문 워크플로우를 자동화합니다.

### 핵심 기능
1. **arXiv 검색**: 주제별 논문 검색 및 필터링
2. **Zotero 추가**: 논문 메타데이터와 PDF를 Zotero 라이브러리에 저장
3. **Obsidian 정리**: 논문 요약을 마크다운 노트로 생성

---

## 프로젝트 구조

```
arxiv-zotero-obsidian/
├── .claude/
│   └── skills/
│       ├── arxiv-search/
│       │   ├── SKILL.md
│       │   └── scripts/search_arxiv.py
│       ├── zotero-add/
│       │   ├── SKILL.md
│       │   └── scripts/add_to_zotero.py
│       └── obsidian-summarize/
│           ├── SKILL.md
│           ├── scripts/create_summary.py
│           └── templates/paper_summary.md
├── src/
│   ├── __init__.py
│   ├── config.py           # 설정 관리
│   ├── arxiv_client.py     # arXiv API 클라이언트
│   ├── zotero_client.py    # Zotero API 클라이언트
│   └── obsidian_writer.py  # Obsidian 마크다운 생성
├── tests/
├── config/
│   └── config.example.yaml
├── pyproject.toml
└── .env.example
```

---

## Skills 아키텍처

### 1. arxiv-search Skill
| 항목 | 내용 |
|------|------|
| **용도** | arXiv에서 논문 검색 |
| **기능** | 키워드 검색, 카테고리 필터, 날짜 필터, 정렬 |
| **출력** | 논문 목록 (ID, 제목, 저자, 초록, PDF URL) |

### 2. zotero-add Skill
| 항목 | 내용 |
|------|------|
| **용도** | Zotero에 논문 추가 |
| **기능** | 컬렉션 생성/선택, 메타데이터 저장, PDF 다운로드 및 첨부 |
| **필요** | Zotero API Key, Library ID |

### 3. obsidian-summarize Skill
| 항목 | 내용 |
|------|------|
| **용도** | Obsidian에 논문 요약 노트 생성 |
| **기능** | 템플릿 기반 마크다운 생성, 프론트매터 포함, Zotero 링크 |
| **필요** | Vault 경로 |

---

## 핵심 의존성

```toml
[project]
dependencies = [
    "arxiv>=2.1.0",         # arXiv API 클라이언트
    "pyzotero>=1.5.0",      # Zotero Web API 클라이언트
    "pyyaml>=6.0",          # 설정 파일 파싱
    "python-dotenv>=1.0.0", # 환경변수 관리
    "rich>=13.0.0",         # CLI 출력 포맷팅
]
```

---

## 설정 파일

### config.yaml
```yaml
arxiv:
  delay_seconds: 3.0        # API 요청 간격 (rate limit 준수)
  default_max_results: 10
  download_dir: "./downloads"

zotero:
  library_id: "YOUR_USER_ID"
  library_type: "user"       # "user" 또는 "group"
  api_key: "${ZOTERO_API_KEY}"
  default_collection: "arXiv Papers"

obsidian:
  vault_path: "/path/to/vault"
  papers_folder: "Papers"
```

### .env
```bash
ZOTERO_API_KEY=your_api_key_here
```

---

## 구현 순서

### Phase 1: 기본 설정
- [ ] 프로젝트 디렉토리 구조 생성
- [ ] pyproject.toml 작성
- [ ] config.py 구현 (YAML + 환경변수 로드)

### Phase 2: 핵심 클라이언트
- [ ] arxiv_client.py - 검색 및 PDF 다운로드
- [ ] zotero_client.py - 컬렉션/아이템 관리, PDF 첨부
- [ ] obsidian_writer.py - 마크다운 파일 생성

### Phase 3: Skills 개발
- [ ] arxiv-search skill (SKILL.md + search_arxiv.py)
- [ ] zotero-add skill (SKILL.md + add_to_zotero.py)
- [ ] obsidian-summarize skill (SKILL.md + create_summary.py + 템플릿)

### Phase 4: 통합 및 테스트
- [ ] 단위 테스트 작성
- [ ] 통합 테스트
- [ ] README.md 작성

---

## 주요 클래스 설계

### ArxivClient
```python
class ArxivClient:
    def search(query, max_results, sort_by, category) -> List[PaperResult]
    def download_pdf(arxiv_id, download_dir) -> str  # 파일 경로 반환
```

### ZoteroClient
```python
class ZoteroClient:
    def find_or_create_collection(name) -> str  # collection_key
    def create_paper_item(title, authors, abstract, ...) -> str  # item_key
    def attach_pdf(item_key, pdf_path) -> bool
```

### ObsidianWriter
```python
class ObsidianWriter:
    def create_summary(arxiv_id, title, authors, ...) -> str  # 파일 경로
```

---

## Obsidian 노트 템플릿

```markdown
---
title: "{{title}}"
authors: [{{authors}}]
arxiv_id: "{{arxiv_id}}"
date_added: {{date}}
tags: [{{tags}}]
zotero_key: "{{zotero_key}}"
---

# {{title}}

> [!info] Paper Overview
> - **Authors**: {{authors}}
> - **arXiv**: [{{arxiv_id}}](https://arxiv.org/abs/{{arxiv_id}})
> - **Zotero**: [Open](zotero://select/items/{{zotero_key}})

## Abstract
{{abstract}}

## Summary
{{summary}}

## Key Findings
- {{finding_1}}
- {{finding_2}}

## Personal Notes
{{notes}}
```

---

## 사전 준비 사항

구현 전에 다음 정보가 필요합니다:

| 항목 | 설명 | 획득 방법 |
|------|------|----------|
| **Zotero API Key** | Zotero Web API 인증 | https://www.zotero.org/settings/keys |
| **Zotero Library ID** | 사용자 라이브러리 식별자 | 위 페이지에서 확인 |
| **Obsidian Vault 경로** | 노트가 저장될 위치 | 기존 vault 경로 |

---

## 예상 사용 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ 사용자: "transformer attention mechanism 관련 논문 찾아줘"    │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    [arxiv-search skill]
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Claude: 검색 결과 10개 표시                                   │
│   [1] Attention Is All You Need                              │
│   [2] BERT: Pre-training of Deep...                          │
│   ...                                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 사용자: "1, 3번 논문 Zotero에 저장해줘"                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    [zotero-add skill]
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Claude: Zotero 'arXiv Papers' 컬렉션에 2개 논문 추가 완료     │
│   - PDF 다운로드 및 첨부 완료                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 사용자: "1번 논문 요약해서 Obsidian에 정리해줘"                │
└─────────────────────────────────────────────────────────────┘
                              ↓
                  [obsidian-summarize skill]
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Claude: Papers/2026-01-11-attention-is-all-you-need.md 생성  │
│   - 요약, 핵심 발견, 방법론 정리 완료                         │
│   - Zotero 링크 포함                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 검증 방법

```bash
# 1. 단위 테스트
pytest tests/ -v

# 2. 통합 테스트 (실제 API 연동)
ZOTERO_API_KEY=xxx pytest tests/test_integration.py -v

# 3. Skills 테스트 (Claude Code 내에서)
# - "quantum computing 논문 검색해줘"
# - "1번 논문 Zotero에 추가해줘"
# - "1번 논문 Obsidian에 정리해줘"
```

---

## 다음 단계

계획 검토 후 구현을 시작하려면:
1. Zotero API Key와 Library ID 준비
2. Obsidian Vault 경로 확인
3. 구현 시작 요청
