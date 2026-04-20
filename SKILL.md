---
name: security-news-feed
version: 2.2.0
description: Automated security news aggregation and summarization module. Collects news from 13 Korean/international security sources (KRCERT, NCSC, Boho, Dailysecu, BoanNews, AhnLab, etc.) → summarizes with GLM-4.7 API (Z.ai) → publishes to Notion/Tistory. Runs hourly. Use when you want to monitor security news, collect Korean security updates, or aggregate news feeds. Triggers: "보안 뉴스", "security news", "뉴스 수집".
---

# Security News Module

## 개요

한국 보안 뉴스 소스 13곳에서 뉴스를 자동으로 수집하고, GLM-4.7 API (Z.ai)로 요약한 후 Notion과 Tistory에 발행하는 모듈입니다.

**주기**: 1시간마다 자동 실행

## 워크플로우

```
13개 보안 뉴스 소스 병렬 크롤링
    ├─ KRCERT (한국인터넷진흥원) - RSS
    ├─ NCSC (국가사이버안보센터) - Selenium
    ├─ Boho (보호나라) - Selenium
    ├─ DailySecu (데일리시큐) - requests
    ├─ BoanNews (보안뉴스) - requests
    ├─ AhnLab (안랩 ASEC) - requests
    ├─ Igloo (이글루시큐리티) - requests
    ├─ KISA (가이드라인) - requests
    ├─ SKShieldus (SK쉴더스) - Selenium
    ├─ Google News - RSS
    ├─ arXiv - API
    ├─ HackerNews - API
    └─ Hadaio - RSS
    ↓
키워드 기반 필터링 (보안 관련 키워드)
    ↓
GLM-4.7 API 요약 (140자 요약 + 상세 분석)
    ↓
Notion 데이터베이스 저장
    ↓
Tistory 블로그 발행 (선택)
```

## 주요 기능

### 1. 뉴스 수집 (Collection)
**13개 한국/국제 보안 뉴스 소스**:

| 소스 | URL | 타입 | 방식 |
|------|-----|------|------|
| KRCERT | https://knvd.krcert.or.kr | 공식 | RSS |
| NCSC | https://www.ncsc.go.kr | 공식 | Selenium |
| Boho | https://www.boho.or.kr | 공식 | Selenium |
| DailySecu | https://dailysecu.com | 민간 | requests |
| BoanNews | https://www.boannews.com | 민간 | requests |
| AhnLab | https://asec.ahnlab.com | 민간 | requests |
| Igloo | https://www.igloosec.com | 민간 | requests |
| KISA | https://www.kisa.or.kr | 공식 | requests |
| SKShieldus | https://www.skshieldus.com | 민간 | Selenium |
| Google News | - | 국제 | RSS |
| arXiv | https://arxiv.org | 국제 | API |
| HackerNews | https://news.ycombinator.com | 국제 | API |
| Hadaio | https://hada.io | 국제 | RSS |

### 2. 키워드 필터링 (Filtering)
**보안 관련 키워드**:
```python
keywords = [
    "취약점", "악성코드", "해킹", "랜섬웨어",
    "보안", "침해", "공격", "암호화",
    "인증", "방화벽", "악성", "피싱",
    "스파이웨어", "트로이목마", "봇넷"
]
```

### 3. GLM-4.7 API 요약 (Summarization)
**요약 구조**:
```
[140자 요약]
- 핵심 내용 3줄 요약

[상세 분석]
- 배경 설명
- 주요 내용
- 시사점
- 대응 방안
```

### 4. Notion 발행 (Notion Publishing)
- **자동 저장**: 수집된 뉴스 자동 저장
- **태그 분류**: 키워드 기반 자동 태그
- **상태 관리**: New → Read → Archived

### 5. Tistory 발행 (Tistory Publishing)
- **선택적 발행**: 중요 뉴스만 발행
- **자동 포맷팅**: 마크다운 → HTML 변환
- **카테고리 분류**: 자동 카테고리 할당

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/rebugui/security-news-feed.git
cd security-news-feed
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`~/.openclaw/workspace/.env` 파일 수정:
```bash
# GLM API (Z.ai)
SECURITY_NEWS_GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4

# Notion API
NOTION_API_KEY=your_notion_api_key
SECURITY_NEWS_DATABASE_ID=your_database_id

# Tistory API (선택)
TISTORY_BLOG_NAME=your_blog_name
```

## 사용법

### 수동 실행
```bash
# 1회 실행
python security_news_aggregator.py --once

# 데몬 모드 (지속 실행)
python security_news_aggregator.py

# 특정 소스만 수집
python security_news_aggregator.py --sources krcert,ncsc
```

### 스케줄러 등록
OpenClaw 스케줄러에 등록하여 자동 실행:

```yaml
# config.yaml
jobs:
  - id: "security_news_aggregator"
    name: "Security News Aggregator - 매 1시간 보안 뉴스 수집"
    enabled: true
    module: "security_news_aggregator.security_news_aggregator"
    function: "main"
    is_async: false
    working_dir: "submodules/security_news_aggregator"
    trigger:
      type: "interval"
      hours: 1
```

## 설정 파일

### `config.py`
```python
# LLM API (Z.ai / GLM)
SECURITY_LLM_API_KEY = os.getenv("SECURITY_NEWS_GLM_API_KEY") or os.getenv("GLM_API_KEY")
SECURITY_LLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
SECURITY_LLM_MODEL = os.getenv("SECURITY_LLM_MODEL", "glm-4.7")
LLM_CALL_DELAY = 3.0  # API 호출 간 딜레이 (Rate limit 방지)

# Notion 설정
NOTION_API_TOKEN = os.getenv("NOTION_API_KEY")
BOANISSUE_DATABASE_ID = os.getenv("SECURITY_NEWS_DATABASE_ID")

# Tistory 설정
TISTORY_BLOG_NAME = os.getenv("TISTORY_BLOG_NAME", "rebugui")
```

## 파일 구조

```
security-news-feed/
├── security_news_aggregator.py  # 메인 실행 파일 (v2.2, Producer-Consumer)
├── config.py                    # 설정 파일
├── requirements.txt             # 의존성
│
├── modules/                     # 기능 모듈
│   ├── base_crawler.py          # 크롤러 ABC
│   ├── llm_handler.py           # GLM API (Z.ai) 요약
│   ├── notion_handler.py        # Notion CRUD + 중복 체크
│   ├── publisher_service.py     # Notion/Tistory 발행
│   ├── log_utils.py             # 구조화 로깅
│   ├── crawlers/                # 뉴스 수집기 (13개)
│   │   ├── krcert.py, ncsc.py, boho.py
│   │   ├── dailysecu.py, boannews.py, ahlab.py
│   │   ├── igloo.py, kisa.py, skshieldus.py
│   │   ├── google_news.py, arxiv.py, hackernews.py
│   │   └── hadaio.py
│   ├── prompts/                 # LLM 프롬프트 템플릿
│   └── analysis/                # 키워드 분석
│
├── data/                        # 데이터 저장
│   └── url_cache.db             # SQLite URL 중복 캐시
│
└── logs/                        # 로그
    └── security_aggregator.log
```

## Notion 데이터베이스 설정

### 필드 구성
- `Title` (제목)
- `Summary` (140자 요약)
- `Content` (상세 분석)
- `Source` (출처)
- `URL` (원문 링크)
- `Tags` (다중 선택)
- `Published` (발행일)
- `Status` (선택: New, Read, Archived)

## 예시 출력

### 수집된 뉴스
```markdown
# 새로운 랜섬웨어, 한국 기업 공격

**요약**: 새로운 랜섬웨어 변종이 한국 기업들을 대상으로 공격을 시작했습니다...

**상세 분석**:
- **배경**: 최근 들어 증가하는 랜섬웨어 공격...
- **주요 내용**: 이 랜섬웨어는...
- **시사점**: 기업들의 보안 강화 필요...
- **대응 방안**: 정기 백업, 보안 패치...

**태그**: #랜섬웨어 #한국 #기업공격

**출처**: KRCERT
**원문**: https://www.krcert.or.kr/...
```

## 실행 통계

### 최근 실행 결과 (2026-03-08 11:58)
```
✅ 수집된 뉴스: 169개
✅ URL 변환 완료: 137개
✅ 키워드 기반 필터링: 169개 처리
✅ GLM-4.7 요약 완료
✅ Notion 저장 완료
```

## 문제 해결

### 뉴스 수집 실패
```bash
# 로그 확인
tail -f logs/security_aggregator.log

# 1회 실행 (디버그)
python security_news_aggregator.py --once --skip-sync
```

### GLM API 오류 (429 Rate Limit)
```bash
# API 키 확인
echo $SECURITY_NEWS_GLM_API_KEY

# LLM_CALL_DELAY 증가 (config.py에서 기본 3.0초)
# 이미 자동 재시도 3회 + 지수 백오프 적용됨
```

### Notion 연결 오류
```bash
# Notion API 키 확인
curl -X POST https://api.notion.com/v1/databases/{database_id}/query \
  -H "Authorization: Bearer {token}" \
  -H "Notion-Version: 2022-06-28"
```

## 의존성

- Python 3.9+
- GLM-4.7 API (Z.ai)
- Notion API
- Tistory API (선택)
- BeautifulSoup4, Requests, Selenium

## API 키 발급

### GLM API (Z.ai)
1. https://open.bigmodel.cn 접속
2. API 키 생성
3. `SECURITY_NEWS_GLM_API_KEY`에 설정

### Notion API (선택)
1. https://www.notion.so/my-integrations 접속
2. 새 통합 생성
3. API 키 복사
4. 데이터베이스에 통합 연결

### Tistory API (선택)
1. https://www.tistory.com/guide/api/register 접속
2. 앱 등록
3. Access Token 발급

## 라이선스

MIT License

## 참고

- **저장소**: https://github.com/rebugui/security_news_aggregator
- **메인 저장소**: https://github.com/rebugui/OpenClaw
