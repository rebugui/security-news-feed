"""SK쉴더스 크롤러 v2 - Tavily 검색 기반 (Akamai WAF 대응)

기존 curl 방식은 Akamai WAF가 차단 (2026년 이후).
Tavily Search API로 최신 글 URL을 수집하고 requests로 내용 파싱.
"""

import json
import re
import os
import requests
from datetime import datetime
from ..base_crawler import BaseCrawler
from ..notion_handler import Duplicate_check
from config import BOANISSUE_DATABASE_ID


TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


class SKShieldusCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.source_name = "SK 쉴더스"
        self.tavily_url = "https://api.tavily.com/search"

    def _search_urls(self):
        """Tavily Search API로 최신 글 URL 수집."""
        if not TAVILY_API_KEY:
            print(f"[{self.source_name}] TAVILY_API_KEY 미설정")
            return []

        try:
            resp = requests.post(
                self.tavily_url,
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": "site:skshieldus.com blog-security",
                    "search_depth": "basic",
                    "max_results": 15,
                    "include_domains": ["skshieldus.com"],
                },
                timeout=15,
            )
            if resp.status_code != 200:
                print(f"[{self.source_name}] Tavily API 오류: {resp.status_code}")
                return []

            data = resp.json()
            urls = []
            for r in data.get("results", []):
                url = r.get("url", "")
                if "/blog-security/" in url:
                    urls.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("content", ""),
                    })

            # 중복 제거
            seen = set()
            unique = []
            for item in urls:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    unique.append(item)
            return unique

        except Exception as e:
            print(f"[{self.source_name}] 검색 실패: {e}")
            return []

    def _fetch_article(self, url):
        """기사 내용 가져오기. Akamai가 차단하면 snippet 사용."""
        title = None
        content = None

        try:
            resp = requests.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/134.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "ko-KR,ko;q=0.9",
                },
                timeout=15,
                allow_redirects=True,
            )
            html = resp.text

            # 제목
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
            if not title:
                og = re.search(
                    r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\'](.*?)["\']',
                    html,
                )
                if og:
                    title = og.group(1).strip()

            # JSON-LD
            jsonld = re.search(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html,
                re.DOTALL,
            )
            if jsonld:
                try:
                    data = json.loads(jsonld.group(1))
                    content = (
                        data.get("description")
                        or data.get("articleBody")
                        or data.get("text")
                    )
                except json.JSONDecodeError:
                    pass

            # meta description fallback
            if not content:
                desc = re.search(
                    r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
                    html,
                )
                if desc:
                    content = desc.group(1).strip()

        except requests.exceptions.RequestException:
            pass  # Akamai 차단 → snippet 사용

        return title, content

    def run(self, publisher_service):
        processing_queue = []
        seen_urls = set()
        scan_total = 0
        scan_success_count = 0
        scan_duplicate_count = 0
        scan_error_count = 0

        try:
            # 1. Tavily 검색으로 최신 글 수집
            print(f"[{self.source_name}] Tavily 검색으로 글 수집 중...")
            articles = self._search_urls()
            scan_total = len(articles)
            print(f"[{self.source_name}] {scan_total}개 글 발견")

            if not articles:
                return {
                    "source": self.source_name,
                    "success": 0,
                    "duplicate": 0,
                    "old": 0,
                    "error": 0,
                    "total": 0,
                }

            # 2. 각 글 처리
            for item in articles:
                url = item["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                try:
                    # Notion 중복 체크
                    dup = Duplicate_check(url, BOANISSUE_DATABASE_ID)
                    if dup != 0:
                        scan_duplicate_count += 1
                        continue

                    # 내용 가져오기
                    title, content = self._fetch_article(url)

                    # 제목이 없으면 검색 결과에서 사용
                    if not title:
                        title = item.get("title", "")
                    if not title:
                        scan_error_count += 1
                        continue

                    # 내용이 없으면 snippet 사용
                    if not content:
                        content = item.get("snippet", "내용 없음")

                    article_data = {
                        "title": title,
                        "content": content[:2000],
                        "url": url,
                        "source": self.source_name,
                        "category": "SK쉴더스",
                        "date": datetime.now().strftime('%Y-%m-%d'),
                        "posting_date": datetime.now(),
                    }

                    if publisher_service:
                        publisher_service.add_article(article_data)
                        scan_success_count += 1
                        print(f"✅ [{self.source_name}] {title[:50]}...")
                    else:
                        processing_queue.append(article_data)
                        scan_success_count += 1

                except Exception as e:
                    scan_error_count += 1
                    continue

            print(
                f"[{self.source_name}] 완료 (성공: {scan_success_count}, "
                f"중복: {scan_duplicate_count}, 에러: {scan_error_count})"
            )

            return {
                "source": self.source_name,
                "success": scan_success_count,
                "duplicate": scan_duplicate_count,
                "old": 0,
                "error": scan_error_count,
                "total": scan_total,
                "queue": processing_queue,
            }

        except Exception as e:
            print(f"[{self.source_name}-FATAL] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "source": self.source_name,
                "success": 0,
                "duplicate": 0,
                "old": 0,
                "error": 1,
                "total": 0,
            }
