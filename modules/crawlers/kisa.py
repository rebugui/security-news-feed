import os
import shutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

from ..base_crawler import BaseCrawler
from ..utils import date_re, send_slack_message, clean_html_content
from ..notion_handler import Duplicate_check
from config import BOANISSUE_DATABASE_ID, GUIDE_DATABASE_ID

class KISACrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.source_name = "KISA 가이드라인"
        self.base_url = "https://www.kisa.or.kr"
        self.target_url = f"{self.base_url}/2060207?page=1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.download_dir = os.path.join("/tmp", "temp_downloads_kisa")

    def run(self, publisher_service):
        processing_queue = []
        seen_urls = set()
        scan_total = 0
        scan_success_count = 0
        scan_duplicate_count = 0
        scan_old_count = 0
        scan_error_count = 0
        process_success_count = 0
        process_error_count = 0

        # 다운로드 디렉토리 정리
        if os.path.exists(self.download_dir):
            shutil.rmtree(self.download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

        print(f"[{self.source_name}] 페이지 로드 중...")

        try:
            # 페이지 로드
            response = requests.get(
                self.target_url, 
                headers=self.headers, 
                timeout=15, 
                verify=False
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 게시물 목록 찾기
            table = soup.find('table')
            if not table:
                print(f"[{self.source_name}] 게시물 테이블을 찾을 수 없습니다.")
                return {
                    "source": self.source_name,
                    "success": 0,
                    "duplicate": 0,
                    "old": 0,
                    "error": 1,
                    "total": 0
                }
            
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
            scan_total = len(rows)
            
            print(f"[{self.source_name}] 총 {scan_total}개의 게시글 발견")

            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                    
                    # 제목과 링크 추출
                    title_cell = cells[1]
                    title_link = title_cell.find('a')
                    
                    if not title_link:
                        continue
                    
                    title = title_link.text.strip()
                    href = title_link.get('href', '')
                    
                    if not title or not href:
                        continue
                    
                    # URL 생성
                    if href.startswith('http'):
                        link_url = href
                    else:
                        link_url = urljoin(self.base_url, href)
                    
                    # 날짜 추출
                    date_cell = cells[2]
                    pub_date_str = date_cell.text.strip()
                    
                    posting_date = date_re(pub_date_str)
                    if not posting_date:
                        scan_error_count += 1
                        continue
                    
                    if not self.is_recent(posting_date):
                        scan_old_count += 1
                        continue
                    
                    # URL 중복 체크
                    if link_url in seen_urls:
                        scan_duplicate_count += 1
                        continue
                    seen_urls.add(link_url)
                    
                    # Notion 중복 체크
                    duplicate_status = Duplicate_check(link_url, GUIDE_DATABASE_ID)
                    if duplicate_status == 0:
                        # 상세 페이지에서 내용 추출
                        final_content = "내용 없음"
                        files_to_upload = []
                        
                        try:
                            detail_resp = requests.get(
                                link_url, 
                                headers=self.headers, 
                                timeout=10, 
                                verify=False
                            )
                            
                            if detail_resp.status_code == 200:
                                detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                                
                                # 본문 추출
                                content_div = (detail_soup.find('div', class_='board_detail_contents') or
                                             detail_soup.find('div', class_='board_view') or
                                             detail_soup.find('div', class_='content'))
                                
                                if content_div:
                                    final_content = clean_html_content(content_div.get_text(separator='\n'))
                                
                                # 첨부 파일 추출 (KISA는 JS 기반 다운로드)
                                attach_section = detail_soup.find('div', class_='board_detail_attach')
                                if not attach_section:
                                    attach_section = detail_soup
                                
                                # 파일 링크 선택자 확장
                                file_links = (attach_section.select('a[href*="download"]') +
                                            attach_section.select('a[href*="#fnPostAttachDownload"]') +
                                            attach_section.select('a.btn-file'))
                                
                                for idx_file, file_link in enumerate(file_links, 1):
                                    href = file_link.get('href', '')
                                    file_name = file_link.get_text(strip=True) or 'attachment'
                                    
                                    # JS 다운로드 링크인 경우: /post/fileDownload 엔드포인트 사용
                                    if href.startswith('#') or 'fnPostAttachDownload' in href:
                                        import re as _re
                                        file_name_text = _re.sub(r'\s*\(.*?(?:MB|KB|GB).*?\)', '', file_name).strip()
                                        
                                        # menuSeq, postSeq 추출
                                        menu_seq_match = _re.search(r'/(\d{7,})/', link_url)
                                        post_seq_match = _re.search(r'postSeq=(\d+)', link_url)
                                        menu_seq = menu_seq_match.group(1) if menu_seq_match else '2060202'
                                        post_seq = post_seq_match.group(1) if post_seq_match else None
                                        
                                        if post_seq:
                                            file_url_to_use = f'{self.base_url}/post/fileDownload?menuSeq={menu_seq}&postSeq={post_seq}&attachSeq={idx_file}&lang_type=KO'
                                            file_name_clean = file_name_text
                                        else:
                                            file_url_to_use = None
                                            file_name_clean = file_name_text
                                    else:
                                        file_url_to_use = urljoin(self.base_url, href)
                                        file_name_clean = file_name
                                    
                                    if file_url_to_use:
                                        try:
                                            dl_resp = requests.get(
                                                file_url_to_use, headers=self.headers,
                                                timeout=30, verify=False, stream=True
                                            )
                                            if dl_resp.status_code == 200 and len(dl_resp.content) > 0:
                                                safe_name = _re.sub(r'[\\/:*?"<>|]', '_', file_name_text)
                                                if not any(safe_name.lower().endswith(ext) for ext in ['.pdf', '.hwp', '.hwpx', '.doc', '.docx', '.zip', '.xlsx', '.pptx']):
                                                    safe_name += '.pdf'
                                                local_path = os.path.join(self.download_dir, safe_name)
                                                with open(local_path, 'wb') as f:
                                                    f.write(dl_resp.content)
                                                if os.path.getsize(local_path) > 0:
                                                    files_to_upload.append({
                                                        'path': local_path,
                                                        'name': safe_name
                                                    })
                                                    print(f'  📄 다운로드 완료: {safe_name} ({os.path.getsize(local_path)} bytes)')
                                                else:
                                                    os.remove(local_path)
                                                    print(f'  ❌ 빈 파일: {safe_name}')
                                            else:
                                                print(f'  ❌ 다운로드 실패: {file_name_text} (status: {dl_resp.status_code}, size: {len(dl_resp.content)})')
                                        except Exception as dl_err:
                                            print(f'  ❌ 다운로드 오류: {file_name_text} - {dl_err}')
                        
                        except Exception as e:
                            print(f"[{self.source_name}-DETAIL] Error: {e}")
                        
                        # 기사 데이터 생성
                        article_data = {
                            'title': title,
                            'content': final_content,
                            'url': link_url,
                            'source': self.source_name,
                            'category': 'KISA',
                            'date': posting_date.strftime('%Y-%m-%d') if posting_date else None,
                            'posting_date': posting_date,
                            'files': files_to_upload
                        }
                        
                        # Publisher Service에 전달
                        if publisher_service:
                            try:
                                publisher_service.add_article(article_data)
                                process_success_count += 1
                                print(f"✅ [{self.source_name}] {title[:50]}...")
                            except Exception as e:
                                process_error_count += 1
                                print(f"❌ [{self.source_name}-PUBLISH] {title[:30]}: {e}")
                        else:
                            processing_queue.append(article_data)
                            process_success_count += 1
                    
                    else:
                        scan_duplicate_count += 1
                
                except Exception as e:
                    scan_error_count += 1
                    print(f"[{self.source_name}-ROW] Error: {e}")
                    continue
            
            print(f"[{self.source_name}] 크롤링 완료")
            
            return {
                "source": self.source_name,
                "success": process_success_count,
                "duplicate": scan_duplicate_count,
                "old": scan_old_count,
                "error": scan_error_count,
                "total": scan_total,
                "queue": processing_queue
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
                "total": 0
            }
