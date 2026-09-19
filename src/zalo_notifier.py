import os
import json
import time
import requests

# Hỗ trợ phát âm thanh còi cảnh báo khẩn cấp trên máy tính Windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class ZaloNotifier:
    """
    Phân hệ Cảnh báo Khẩn cấp & Tích hợp Zalo Open API (Zalo Notifier Module)
    - Nhận lệnh kích hoạt khi xảy ra cú ngã (`Falling`).
    - Hỗ trợ 3 chế độ gửi thông báo linh hoạt:
      1. Mode 'mock': Lưu snapshot + clip 3-5s vào data/outputs/, phát âm thanh còi báo động khẩn cấp qua loa PC.
      2. Mode 'sandbox': Sử dụng Zalo Developer Test Token gửi trực tiếp tin nhắn + ảnh/video về Zalo cá nhân.
      3. Mode 'oa': Gọi Zalo Official Account Open API REST payload khi đăng ký doanh nghiệp.
    """
    def __init__(self, config_path="config/zalo_config.json", logger=None):
        self.config_path = config_path
        self.logger = logger
        
        self.mode = "mock"
        self.enable_pc_audio_alarm = True
        self.zalo_access_token = ""
        self.receiver_phone_id = ""
        self.mock_save_dir = "data/outputs"
        
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.mode = cfg.get("mode", "mock")
                    self.enable_pc_audio_alarm = cfg.get("enable_pc_audio_alarm", True)
                    self.zalo_access_token = cfg.get("zalo_access_token", "")
                    self.receiver_phone_id = cfg.get("receiver_phone_id", "")
                    self.mock_save_dir = cfg.get("mock_save_dir", "data/outputs")
                    
                if self.logger:
                    self.logger.info(f"Đã tải cấu hình Zalo Notifier [Mode: {self.mode}]")
                    if self.zalo_access_token and not self.zalo_access_token.startswith("YOUR_"):
                        self.validate_token()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Lỗi đọc zalo_config.json: {e}. Chuyển sang chế độ 'mock'.")
        else:
            if self.logger:
                self.logger.warning("Không tìm thấy file zalo_config.json, tự động khởi tạo mặc định mode 'mock'.")

    def validate_token(self):
        """Xác thực Token qua Zalo Graph API"""
        try:
            url = "https://graph.zalo.me/v2.0/me"
            headers = {"access_token": self.zalo_access_token}
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            if data.get("error") == 0:
                user_name = data.get("name", "N/A")
                user_id = data.get("id", "N/A")
                if self.logger:
                    self.logger.info(f" Kết nối thành công Zalo API cá nhân! Chủ tài khoản: {user_name} (Zalo ID: {user_id})")
                return True, data
            else:
                if self.logger:
                    self.logger.warning(f"Zalo Token cá nhân phản hồi: {data.get('message')}")
                return False, data
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi xác thực Zalo Token: {e}")
            return False, None

    def trigger_pc_audio_alarm(self):
        """Phát âm thanh còi báo động khẩn cấp qua loa máy tính"""
        if not self.enable_pc_audio_alarm:
            return
            
        try:
            if HAS_WINSOUND:
                for _ in range(3):
                    winsound.Beep(1500, 300)
                    time.sleep(0.1)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Không thể phát âm thanh còi báo động: {e}")

    def send_alert(self, snapshot_path, video_path, metrics=None):
        """
        Gửi thông báo sự cố té ngã khẩn cấp kèm hình ảnh/video bằng chứng.
        """
        timestamp_str = time.strftime("%H:%M:%S - %d/%m/%Y")
        alert_msg = (
            f" CẢNH BÁO KHẨN CẤP: PHÁT HIỆN TÉ NGÃ NGƯỜI CAO TUỔI!\n"
            f" Thời gian phát hiện: {timestamp_str}\n"
            f" Vị trí: Môi trường giám sát gia đình\n"
            f" Bằng chứng đính kèm: 1 Ảnh chụp sự cố + 1 Clip Video (3-5s)\n"
            f" Vui lòng kiểm tra và ứng cứu ngay lập tức!"
        )
        
        # 1. Luôn kích hoạt âm thanh còi cảnh báo khẩn cấp tại chỗ
        self.trigger_pc_audio_alarm()
        
        # 2. Xử lý gửi cảnh báo theo Mode đã cấu hình
        if self.mode == "zalo_personal":
            try:
                from zalo_personal_automation import ZaloPersonalAutomation
                zalo_auto = ZaloPersonalAutomation(
                    profile_dir="zalo_browser_profile",
                    target_chat=self.receiver_phone_id if self.receiver_phone_id and not self.receiver_phone_id.startswith("84") else "Truyền File",
                    logger=self.logger
                )
                success = zalo_auto.send_alert_personal(alert_msg, snapshot_path, video_path)
                if not success:
                    self._send_mock_alert(alert_msg, snapshot_path, video_path)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Lỗi gửi Zalo Personal: {e}")
                self._send_mock_alert(alert_msg, snapshot_path, video_path)
        elif self.mode == "telegram":
            success = self._send_telegram_bot(alert_msg, snapshot_path, video_path)
            if not success:
                self._send_mock_alert(alert_msg, snapshot_path, video_path)
        elif self.mode in ["sandbox", "oa"]:
            success = self._send_zalo_api(alert_msg, snapshot_path, video_path)
            if not success:
                if self.logger:
                    self.logger.warning("Do Zalo hạn chế API cho tài khoản cá nhân (yêu cầu Zalo OA Doanh Nghiệp), hệ thống kích hoạt Fallback Mock Alert + Còi báo động PC.")
                self._send_mock_alert(alert_msg, snapshot_path, video_path)
        else:
            self._send_mock_alert(alert_msg, snapshot_path, video_path)


    def _send_telegram_bot(self, alert_msg, snapshot_path, video_path):
        """Gửi thông báo tức thời kèm ảnh snapshot + video 3-5s về điện thoại qua Telegram Bot"""
        telegram_token = self.zalo_access_token # Dùng chung trường token hoặc telegram_bot_token
        chat_id = self.receiver_phone_id
        
        if not telegram_token or not chat_id:
            if self.logger:
                self.logger.error("Chưa cấu hình Telegram Bot Token hoặc Chat ID!")
            return False
            
        try:
            if self.logger:
                self.logger.info("Đang gửi thông báo khẩn cấp + bằng chứng về điện thoại qua Telegram Bot...")
                
            # 1. Gửi tin nhắn text
            url_msg = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(url_msg, json={"chat_id": chat_id, "text": alert_msg}, timeout=5)
            
            # 2. Gửi ảnh snapshot
            if snapshot_path and os.path.exists(snapshot_path):
                url_photo = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"
                with open(snapshot_path, 'rb') as photo_file:
                    requests.post(url_photo, data={"chat_id": chat_id, "caption": "📸 Ảnh bằng chứng cú ngã"}, files={"photo": photo_file}, timeout=10)
                    
            # 3. Gửi video clip 3-5s
            if video_path and os.path.exists(video_path):
                url_video = f"https://api.telegram.org/bot{telegram_token}/sendVideo"
                with open(video_path, 'rb') as video_file:
                    requests.post(url_video, data={"chat_id": chat_id, "caption": " Clip video bằng chứng (3-5s)"}, files={"video": video_file}, timeout=15)
                    
            if self.logger:
                self.logger.info(" ĐÃ GỬI THÀNH CÔNG THÔNG BÁO + ẢNH + VIDEO VỀ ĐIỆN THOẠI!")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi gửi Telegram Bot: {e}")
            return False

    def _send_mock_alert(self, alert_msg, snapshot_path, video_path):
        """Chế độ mô phỏng cảnh báo cục bộ"""
        if self.logger:
            self.logger.alert("=== [CẢNH BÁO SỰ CỐ NGÃ ĐÃ ĐƯỢC GHI NHẬN] ===")
            self.logger.info(alert_msg)
            self.logger.info(f"📁 Ảnh bằng chứng sự cố: {os.path.abspath(snapshot_path) if snapshot_path else 'N/A'}")
            self.logger.info(f"📁 Clip video bằng chứng: {os.path.abspath(video_path) if video_path else 'N/A'}")

    def _send_zalo_api(self, alert_msg, snapshot_path, video_path):
        """Thực hiện cuộc gọi Zalo Open API gửi tin nhắn khẩn cấp kèm ảnh/video"""
        url = "https://openapi.zalo.me/v3.0/oa/message/cs"
        headers = {
            "access_token": self.zalo_access_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "recipient": {
                "user_id": self.receiver_phone_id
            },
            "message": {
                "text": alert_msg
            }
        }
        
        try:
            if self.logger:
                self.logger.info("Đang kết nối Zalo API Endpoint...")
                
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            res_json = response.json()
            
            if response.status_code == 200 and res_json.get("error") == 0:
                if self.logger:
                    self.logger.info("Đã gửi thành công tin nhắn cảnh báo qua Zalo Open API!")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Zalo API Phản hồi: {res_json}")
                return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Không thể kết nối Zalo API Endpoint: {e}")
            return False


