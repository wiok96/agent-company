"""
نظام التسجيل لـ AACS V0
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "aacs", level: int = logging.INFO) -> logging.Logger:
    """إعداد نظام التسجيل"""
    
    # إنشاء logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # تجنب إضافة handlers متعددة
    if logger.handlers:
        return logger
    
    # إعداد التنسيق
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # handler للكونسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # handler للملف (اختياري)
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"aacs_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        # إذا فشل إنشاء ملف السجل، نكمل بدونه
        logger.warning(f"تعذر إنشاء ملف السجل: {e}")
    
    return logger


def redact_sensitive_data(message: str) -> str:
    """تنقية البيانات الحساسة من الرسائل"""
    import re
    
    # أنماط البيانات الحساسة
    patterns = [
        (r'(api[_-]?key["\s]*[:=]["\s]*)([^"\s]+)', r'\1***REDACTED***'),
        (r'(token["\s]*[:=]["\s]*)([^"\s]+)', r'\1***REDACTED***'),
        (r'(password["\s]*[:=]["\s]*)([^"\s]+)', r'\1***REDACTED***'),
        (r'(secret["\s]*[:=]["\s]*)([^"\s]+)', r'\1***REDACTED***'),
        (r'(gsk_[a-zA-Z0-9]+)', r'***REDACTED_GROQ_KEY***'),
        (r'(sk-[a-zA-Z0-9]+)', r'***REDACTED_OPENAI_KEY***'),
        (r'(ghp_[a-zA-Z0-9]+)', r'***REDACTED_GITHUB_TOKEN***'),
    ]
    
    result = message
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


class SecureLogger:
    """Logger آمن ينقي البيانات الحساسة"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def info(self, message: str):
        self.logger.info(redact_sensitive_data(message))
    
    def warning(self, message: str):
        self.logger.warning(redact_sensitive_data(message))
    
    def error(self, message: str):
        self.logger.error(redact_sensitive_data(message))
    
    def debug(self, message: str):
        self.logger.debug(redact_sensitive_data(message))
    
    def exception(self, message: str):
        self.logger.exception(redact_sensitive_data(message))