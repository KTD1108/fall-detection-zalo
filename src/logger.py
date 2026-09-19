import os
import logging
from datetime import datetime

class SystemLogger:
    """
    Phân hệ Ghi nhật ký thực nghiệm (Logger Module)
    Ghi vết các sự kiện vận hành, cảnh báo sự cố té ngã và chỉ số hệ thống (FPS, Confidence, Latency)
    vào file logs/system_events.log và hiển thị trực quan lên Terminal.
    """
    def __init__(self, log_file_path="logs/system_events.log"):
        self.log_file_path = log_file_path
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        self.logger = logging.getLogger("FallDetectionSystem")
        self.logger.setLevel(logging.DEBUG)
        
        # Format nhật ký
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Stream (Console) handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Thêm handler nếu chưa có
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def alert(self, msg):
        # Mức log khẩn cấp dành riêng cho sự cố ngã
        self.logger.critical(f" ALERT TRIGGERED: {msg}")

    def error(self, msg):
        self.logger.error(f"❌ ERROR: {msg}")
