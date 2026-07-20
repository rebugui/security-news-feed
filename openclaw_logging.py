# Compatibility shim for openclaw_logging (OpenClaw removed 2026-07-10)
# Provides minimal interface so security-news-feed can run without OpenClaw
import logging
import os

def setup_skill_logger(name):
    """Create a standard Python logger"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    return logger

class Metrics:
    """Simple metrics collector"""
    def __init__(self):
        self.data = {}
    
    def increment(self, key, value=1):
        self.data[key] = self.data.get(key, 0) + value
    
    def record(self, key, value):
        self.data[key] = value
    
    def get(self, key):
        return self.data.get(key, 0)

class LogContext:
    """Minimal log context"""
    def __init__(self, logger):
        self.logger = logger
    
    def log_event(self, event_type, **kwargs):
        self.logger.debug(f"[{event_type}] {kwargs}")
