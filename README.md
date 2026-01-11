# arXiv-Zotero-Obsidian Agent

Claude Code 기반의 AI 에이전트로, 학술 논문 워크플로우를 자동화합니다.

## 기능

- **arXiv 검색**: 키워드로 논문 검색, 카테고리/날짜 필터링
- **Zotero 추가**: 논문 메타데이터 + PDF 자동 저장
- **Obsidian 정리**: 논문 요약 노트 자동 생성

---

## 설치

### 1. 의존성 설치

```bash
cd /Users/varde/code/arxiv-zotero-obsidian
pip install arxiv pyzotero python-dotenv rich
```

### 2. 설정 파일 구성

**config/config.json:**
```json
{
  "arxiv": {
    "delay_seconds": 3.0,
    "default_max_results": 10,
    "download_dir": "./downloads"
  },
  "zotero": {
    "library_id": "YOUR_LIBRARY_ID",
    "library_type": "user",
    "api_key": "${ZOTERO_API_KEY}",
    "default_collection": "arXiv Papers"
  },
  "obsidian": {
    "vault_path": "/path/to/your/vault",
    "papers_folder": "Papers"
  }
}
```

**.env 파일:**
```bash
ZOTERO_API_KEY=your_api_key_here
```

### 3. Zotero 설정 확인

1. https://www.zotero.org/settings/keys 접속
2. API Key 생성 (Read/Write 권한)
3. "Your userID for use in API calls is XXXXXX" 확인 → `library_id`에 입력

---

## 사용법

### 방법 1: Claude Code Skills (추천)

Claude Code에서 자연어로 요청하면 자동으로 Skills가 실행됩니다:

```
"transformer 관련 최신 논문 찾아줘"
"1번 논문 Zotero에 저장해줘"
"저장한 논문 Obsidian에 요약해줘"
```

### 방법 2: 직접 스크립트 실행

#### 논문 검색

```bash
# 기본 검색
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "deep learning"

# 옵션 포함 검색
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "large language models" \
  --max-results 5 \
  --category "cs.CL" \
  --date-from "2024-01-01" \
  --sort-by "submitted_date"

# JSON 출력
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "attention mechanism" \
  --output json
```

**검색 옵션:**
| 옵션 | 설명 | 예시 |
|------|------|------|
| `--query` | 검색어 (필수) | "transformer" |
| `--max-results` | 결과 수 | 10 |
| `--category` | arXiv 카테고리 | cs.AI, cs.LG, physics.cond-mat |
| `--date-from` | 시작 날짜 | 2024-01-01 |
| `--date-to` | 종료 날짜 | 2024-12-31 |
| `--sort-by` | 정렬 기준 | relevance, submitted_date, last_updated |
| `--output` | 출력 형식 | text, json |

**검색 쿼리 문법:**
- `ti:keyword` - 제목에서 검색
- `au:name` - 저자 검색
- `abs:keyword` - 초록에서 검색
- `cat:category` - 카테고리 필터

```bash
# 저자로 검색
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py --query "au:Hinton"

# 제목 + 초록 조합
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py --query "ti:transformer AND abs:attention"
```

#### Zotero에 논문 추가

```bash
python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "1706.03762" \
  --title "Attention Is All You Need" \
  --authors "Ashish Vaswani,Noam Shazeer,Niki Parmar" \
  --abstract "The dominant sequence transduction models..." \
  --published "2017-06-12" \
  --collection "Transformers" \
  --tags "transformer,attention,nlp"
```

**Zotero 옵션:**
| 옵션 | 설명 | 필수 |
|------|------|------|
| `--arxiv-id` | arXiv 논문 ID | O |
| `--title` | 논문 제목 | O |
| `--authors` | 저자 (쉼표 구분) | O |
| `--abstract` | 초록 | X |
| `--published` | 출판일 | X |
| `--collection` | Zotero 컬렉션명 | X |
| `--tags` | 태그 (쉼표 구분) | X |
| `--skip-pdf` | PDF 다운로드 건너뛰기 | X |
| `--doi` | DOI | X |

#### Obsidian에 요약 노트 생성

```bash
python3 .claude/skills/obsidian-summarize/scripts/create_summary.py \
  --arxiv-id "1706.03762" \
  --title "Attention Is All You Need" \
  --authors "Ashish Vaswani,Noam Shazeer,Niki Parmar" \
  --abstract "The dominant sequence transduction models..." \
  --published "2017-06-12" \
  --zotero-key "ZKPFEBEH" \
  --summary "Transformer 아키텍처 제안. Self-attention으로 시퀀스 처리." \
  --key-findings "Self-attention이 RNN 대체|병렬 학습 가능|번역 SOTA" \
  --tags "transformer,attention,nlp"
```

**Obsidian 옵션:**
| 옵션 | 설명 | 필수 |
|------|------|------|
| `--arxiv-id` | arXiv 논문 ID | O |
| `--title` | 논문 제목 | O |
| `--authors` | 저자 (쉼표 구분) | O |
| `--abstract` | 원본 초록 | X |
| `--published` | 출판일 | X |
| `--zotero-key` | Zotero 아이템 키 (링크용) | X |
| `--summary` | 요약 내용 | X |
| `--key-findings` | 핵심 발견 (파이프 구분) | X |
| `--methodology` | 방법론 | X |
| `--contributions` | 주요 기여 | X |
| `--limitations` | 한계점 | X |
| `--future-work` | 향후 연구 방향 | X |
| `--personal-notes` | 개인 메모 | X |
| `--tags` | 태그 (쉼표 구분) | X |

---

## 전체 워크플로우 예시

```bash
# 1. 논문 검색
python3 .claude/skills/arxiv-search/scripts/search_arxiv.py \
  --query "state space models" \
  --max-results 3

# 출력:
# [1] Mamba: Linear-Time Sequence Modeling...
#     arXiv ID: 2312.00752
#     ...

# 2. 원하는 논문 Zotero에 추가
python3 .claude/skills/zotero-add/scripts/add_to_zotero.py \
  --arxiv-id "2312.00752" \
  --title "Mamba: Linear-Time Sequence Modeling with Selective State Spaces" \
  --authors "Albert Gu,Tri Dao" \
  --collection "SSM Research"

# 출력:
# Created Zotero item: 7ASRMNCJ
# PDF attached successfully

# 3. Obsidian에 요약 노트 생성
python3 .claude/skills/obsidian-summarize/scripts/create_summary.py \
  --arxiv-id "2312.00752" \
  --title "Mamba: Linear-Time Sequence Modeling with Selective State Spaces" \
  --authors "Albert Gu,Tri Dao" \
  --zotero-key "7ASRMNCJ" \
  --summary "Selective SSM을 제안하여 Transformer의 대안 제시" \
  --key-findings "선형 시간 복잡도|선택적 상태 공간|긴 시퀀스 처리 효율적"
```

---

## 프로젝트 구조

```
arxiv-zotero-obsidian/
├── .claude/skills/           # Claude Code Skills
│   ├── arxiv-search/         # 논문 검색
│   ├── zotero-add/           # Zotero 추가
│   └── obsidian-summarize/   # Obsidian 요약
├── src/                      # 핵심 모듈
│   ├── arxiv_client.py       # arXiv API 클라이언트
│   ├── zotero_client.py      # Zotero API 클라이언트
│   ├── obsidian_writer.py    # Obsidian 마크다운 생성
│   └── config.py             # 설정 관리
├── config/
│   └── config.json           # 설정 파일
├── downloads/                # 다운로드된 PDF
└── .env                      # API 키 (git 제외)
```

---

## arXiv 카테고리 참고

| 카테고리 | 분야 |
|----------|------|
| cs.AI | Artificial Intelligence |
| cs.CL | Computation and Language (NLP) |
| cs.CV | Computer Vision |
| cs.LG | Machine Learning |
| cs.NE | Neural and Evolutionary Computing |
| stat.ML | Machine Learning (Statistics) |
| physics.cond-mat | Condensed Matter |
| math.* | Mathematics |

전체 목록: https://arxiv.org/category_taxonomy

---

## 문제 해결

### Zotero API 오류
```
Error: Zotero API key not configured
```
→ `.env` 파일에 `ZOTERO_API_KEY` 설정 확인

### PDF 첨부 실패
```
Warning: Failed to attach PDF
```
→ Zotero API Key에 파일 업로드 권한 확인

### Obsidian 경로 오류
```
Error: Obsidian vault not found
```
→ `config/config.json`의 `vault_path` 경로 확인

---

## 라이선스

MIT License
