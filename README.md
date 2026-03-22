# Security News Feed

[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/rebugui/security-news-feed)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 한국 보안 뉴스 소스 11곳에서 뉴스를 자동으로 수집하고, Gemini API로 요약한 후 Notion과 Tistory에 발행하는 모듈

## 개요

한국 보안 뉴스 소스 11곳에서 뉴스를 자동으로 수집하고, Gemini API로 요약한 후 Notion과 Tistory에 발행하는 모듈입니다.

**주기**: 3시간마다 자동 실행 (cron)

## 워크플로우

```
11개 보안 뉴스 소스 병렬 크롤링
    ├─ KRCERT (한국인터넷진흥원)
    ├─ NCSC (국가사이버안보센터)
    ├─ Boho (보호나라)
    ├─ Dailysec
    ├─ KISA
    ├─ K-shield
    ├─ KrCert
    ├─ Notice
    ├─ Boho2
    ├─ Krcert2
    └─ Ncsc2
    ↓
키워드 기반 필터링 (보안 관련 키워드)
    ↓
Gemini API 요약 (140자 요약 + 상세 분석)
    ↓
Notion 데이터베이스 저장
    ↓
Tistory 블로그 발행 (선택)
```

## 주요 기능

### 1. 뉴스 수집 (Collection)
**11개 한국 보안 뉴스 소스**:

| 소스 | URL | 타입 |
|------|-----|------|
| KRCERT | https://www.krcert.or.kr | 공식 |
| NCSC | https://www.ncsc.go.kr | 공식 |
| Boho | https://www.boho.or.kr | 공식 |
| Dailysec | https://dailysecu.com | 민간 |
| KISA | https://www.kisa.or.kr | 공식 |
| K-shield | https://k-shield.or.kr | 공식 |

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

### 3. Gemini API 요약 (Summarization)
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

## 설치

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
```bash
cp .env.example .env
```

`.env` 파일 수정:
```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Notion API
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id

# Tistory API (선택)
TISTORY_ACCESS_TOKEN=your_access_token
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

### Cron 등록
```bash
# crontab -e
0 */3 * * * cd /path/to/security-news-feed && /usr/bin/python3 security_news_aggregator.py --once >> /tmp/security-news-feed.log 2>&1
```

## 설정 파일

### `config.py`
```python
# 뉴스 소스 설정
NEWS_SOURCES = {
    'krcert': {
        'url': 'https://www.krcert.or.kr',
        'type': 'rss',
        'enabled': True
    },
    'ncsc': {
        'url': 'https://www.ncsc.go.kr',
        'type': 'rss',
        'enabled': True
    },
    # ...
}
```

## 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 저장소

- GitHub: https://github.com/rebugui/security-news-feed
