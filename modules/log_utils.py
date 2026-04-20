# modules/log_utils.py
"""
구조화된 로깅 모듈
openclaw_logging 중앙 모듈을 사용하되, 기존 인터페이스 유지
"""
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime

# openclaw_logging 경로 추가
scripts_path = Path.home() / '.openclaw' / 'workspace' / 'scripts'
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

from openclaw_logging import setup_skill_logger, Metrics, LogContext as _BaseLogContext

# 중앙 로거 사용
logger = setup_skill_logger('security-news-feed')

# Suppress WDM (WebDriver Manager) logs
import logging
logging.getLogger('WDM').setLevel(logging.WARNING)
logging.getLogger('webdriver_manager').setLevel(logging.WARNING)


# 전역 메트릭 인스턴스
metrics = Metrics()


class LogContext:
    """
    구조화된 로그 컨텍스트
    기존 정적 메서드 인터페이스 유지 (하위 호환)
    """
    _ctx = _BaseLogContext(logger)

    @staticmethod
    def log_event(event_type: str, **kwargs):
        LogContext._ctx.log_event(event_type, **kwargs)


# 편의 로깅 함수들 (기존 인터페이스 유지)
def log_api_call_start(operation: str, title: Optional[str] = None, input_length: int = 0):
    """API 호출 시작 로그"""
    LogContext.log_event('api_call',
                       operation=operation,
                       status='started',
                       title=title,
                       input_length=input_length)


def log_api_call_end(operation: str, duration: float, title: Optional[str] = None):
    """API 호출 종료 로그"""
    metrics.record_api_call(operation, duration)
    metrics.record_success()
    LogContext.log_event('api_call',
                       operation=operation,
                       status='completed',
                       title=title,
                       duration=duration)


def log_api_call_error(operation: str, error: Exception, title: Optional[str] = None):
    """API 호출 에러 로그"""
    metrics.record_error()
    LogContext.log_event('error',
                       stage=f'api_call_{operation}',
                       title=title,
                       error=str(error))


def log_queue_add(title: str, queue_size: int):
    """큐 추가 로그"""
    LogContext.log_event('queue_event',
                       action='add',
                       title=title,
                       queue_size=queue_size)


def log_queue_take(title: str, queue_size: int, wait_time: float = 0):
    """큐 가져오기 로그"""
    metrics.record_queue_wait(wait_time)
    LogContext.log_event('queue_event',
                       action='take',
                       title=title,
                       queue_size=queue_size)


def log_processing_start(source: str, title: str):
    """처리 시작 로그"""
    LogContext.log_event('processing',
                       stage='start',
                       source=source,
                       title=title)


def log_processing_end(source: str, title: str, duration: float):
    """처리 종료 로그"""
    LogContext.log_event('processing',
                       stage='complete',
                       source=source,
                       title=title,
                       duration=duration)


def log_processing_error(source: str, title: str, error: Exception, stage: str = 'unknown'):
    """처리 에러 로그"""
    metrics.record_error()
    LogContext.log_event('error',
                       stage=stage,
                       source=source,
                       title=title,
                       error=str(error))


def log_crawler_result(source: str, success: int, duplicate: int, old: int, error: int, total: int):
    """크롤러 결과 로그"""
    LogContext.log_event('crawler_result',
                       source=source,
                       success=success,
                       duplicate=duplicate,
                       old=old,
                       error=error,
                       total=total)


def print_metrics_summary():
    """메트릭 요약 출력"""
    summary = metrics.get_summary()

    logger.info("=" * 70)
    logger.info("성능 메트릭 요약")
    logger.info("=" * 70)
    logger.info(f"기준 시간: {summary['timestamp']}")

    for operation, data in summary['api_calls'].items():
        logger.info(f"  {operation}: 호출 {data['count']}회, 평균 {data['avg_time']:.2f}초, 총 {data['total_time']:.2f}초")

    if summary['queue']['avg_wait_time']:
        logger.info(f"  큐 평균 대기: {summary['queue']['avg_wait_time']:.2f}초 ({summary['queue']['total_wait_events']}건)")

    logger.info(f"  성공: {summary['success_rate']['success']} | 실패: {summary['success_rate']['error']} | 성공률: {summary['success_rate']['rate']:.2%}")
    logger.info("=" * 70)
