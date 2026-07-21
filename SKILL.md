---
name: security-news-feed
version: 3.0.0
description: Automated security news aggregation and summarization. Collects from 13 Korean/international sources, summarizes with local Ollama gemma4, publishes to Notion. Runs hourly via Hermes cron. Triggers include 보안 뉴스, security news, 뉴스 수집, 보안뉴스.
---

# Security News Feed

## 개요

한국 보안 뉴스 소스 13곳에서 뉴스를 자동으로 수집하고, **로컬 Ollama (gemma4-uncensored-agg)** 로 요약한 후 Notion에 발행하는 모듈.

**실행 방식**: Hermes cron (no_agent script 모드)  
**주기**: 1시간마다  
**저장소**: https://github.com/rebugui/security-news-feed  
**설치 경로**: `~/.hermes/skills/security-news-feed/`

## 마이그레이션 (OpenClaw → Hermes, 2026-07)

| 항목 | 기존 (OpenClaw) | 현재 (Hermes) |
|------|----------------|---------------|
| 실행 경로 | `submodules/security_news_aggregator/` | `~/.hermes/skills/security-news-feed/` |
| LLM | Z.AI GLM-4.7 | Ollama gemma4-uncensored-agg:e4b |
| LLM URL | `api.z.ai/.../v4/chat/completions` | `localhost:11434/v1/chat/completions` |
| 로깅 | `openclaw_logging` | 호환 shim (`openclaw_logging.py`) |
| 스케줄러 | OpenClaw scheduler | Hermes cronjob (`4e87f479540e`) |
| 환경변수 | `~/.openclaw/workspace/.env` | `~/.hermes/.skills.env` (symlink) |
| Python | /usr/bin/python3 | /opt/homebrew/bin/python3.11 |

## 설치 및 복구

### GitHub에서 클론
```bash
cd ~/.hermes
git clone https://github.com/rebugui/security-news-feed.git skills/security-news-feed
```

### 의존성
```bash
pip3.11 install -r requirements.txt
pip3.11 install feedparser
```

### 환경변수
`~/.hermes/.skills.env` 필요:
```
NOTION_API_KEY=ntn_...
SECURITY_NEWS_DATABASE_ID=...
```

프로젝트 디렉토리에 symlink:
```bash
cd ~/.hermes/skills/security-news-feed
ln -sf ~/.hermes/.skills.env .env
```

### OpenClaw 의존성 제거
- `openclaw_logging.py` — 표준 logging 기반 호환 shim 생성
- `modules/log_utils.py` — import 경로를 프로젝트 디렉토리로 변경

### Ollama 설정
`modules/llm_handler.py`:
```python
DEFAULT_MODEL = "gemma4-uncensored-agg:e4b"
ZAI_API_URL = "http://localhost:11434/v1/chat/completions"
# Authorization 헤더 불필요
headers = {"Content-Type": "application/json"}
```

### Cron 스크립트
`~/.hermes/scripts/run-security-news-feed.sh`:
```bash
SKILL_DIR="$HOME/.hermes/skills/security-news-feed"
source "$HOME/.hermes/.skills.env" 2>/dev/null
cd "$SKILL_DIR"
exec /opt/homebrew/bin/python3.11 "$SKILL_DIR/security_news_aggregator.py" --once
```

## 워크플로우

13개 보안 뉴스 소스 병렬 크롤링 → 키워드 필터링 → Ollama gemma4 요약 → Notion 저장

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| "No such file or directory" | OpenClaw 삭제로 `openclaw-imports/` 소실 | GitHub 재클론 + 경로 수정 |
| `ModuleNotFoundError: openclaw_logging` | 호환 shim 없음 / import 경로 오래됨 | `openclaw_logging.py` 생성 + log_utils.py 경로 수정 |
| `ModuleNotFoundError: feedparser` | 미설치 | `pip3.11 install feedparser` |
| `NOTION_API_TOKEN` 누락 | `.env` symlink 없음 | `ln -sf ~/.hermes/.skills.env .env` |
| Ollama 응답 느림 | gemma4 6.8GB cold start | 첫 실행 후 warm 유지됨 |

## 관련 Cron

| Job ID | 이름 | 일정 |
|--------|------|------|
| `4e87f479540e` | security-news-feed | 매 60분 |
| `e892c2cdb317` | kisa-guideline | 매일 09:00 |

## 참고

- **GitHub**: https://github.com/rebugui/security-news-feed
- **Skill path**: `~/.hermes/skills/security-news-feed/`
- **Cron script**: `~/.hermes/scripts/run-security-news-feed.sh`
