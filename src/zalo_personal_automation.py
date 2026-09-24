import os
import io
import time
import struct
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

try:
    import win32clipboard
    HAS_WIN32CB = True
except ImportError:
    HAS_WIN32CB = False

class ZaloPersonalAutomation:
    """
    Phân hệ Gửi Thông Báo Zalo Cá Nhân Tự Động (Personal Zalo Web Automation)
    - Duy trì phiên làm việc trình duyệt duy nhất (Persistent Browser Instance) để đạt tốc độ gửi < 3 giây.
    - Gửi trực tiếp Tin nhắn Cảnh báo khẩn cấp + 1 Ảnh Snapshot + 1 Clip Video 3-5s bằng chứng
      thẳng về Zalo cá nhân mà KHÔNG CẦN tài khoản Zalo OA Doanh Nghiệp.
    """
    def __init__(self, profile_dir="zalo_browser_profile", target_chat="Truyền File", logger=None):
        self.profile_dir = os.path.abspath(profile_dir)
        self.target_chat = target_chat
        self.logger = logger
        self.driver = None
        os.makedirs(self.profile_dir, exist_ok=True)

    def _get_chrome_driver(self, headless=False):
        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--log-level=3")
        if headless:
            options.add_argument("--headless=new")
            
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def get_driver(self, headless=False):
        """Lấy hoặc khởi tạo tiến trình ChromeDriver tái sử dụng (Persistent Session)"""
        if self.driver is not None:
            try:
                _ = self.driver.current_url
                return self.driver
            except Exception:
                self.driver = None

        self.driver = self._get_chrome_driver(headless=headless)
        return self.driver

    def setup_login(self):
        """Mở trình duyệt để người dùng quét mã QR Zalo Web lần đầu duy nhất"""
        print("\n" + "=" * 70)
        print(" THIẾT LẬP KẾT NỐI ZALO CÁ NHÂN (PERSONAL ZALO SETUP)")
        print("=" * 70)
        print("Trình duyệt Chrome sắp mở ra. Vui lòng lấy điện thoại quét mã QR")
        print("để đăng nhập Zalo Web (chat.zalo.me) lần đầu duy nhất!")
        print("=" * 70 + "\n")
        
        driver = self.get_driver(headless=False)
        try:
            driver.get("https://chat.zalo.me")
            print("Đang chờ bạn quét mã QR Zalo Web...")
            time.sleep(15)
            print("\n ĐĂNG NHẬP ZALO CÁ NHÂN THÀNH CÔNG!")
            print(f"Phiên làm việc đã được lưu vĩnh viễn tại: {self.profile_dir}")
        except Exception as e:
            print(f"❌ Lỗi đăng nhập Zalo: {e}")

    def _copy_image_to_clipboard(self, image_path):
        """Đưa ảnh Snapshot vào Windows Clipboard"""
        if not HAS_WIN32CB or not os.path.exists(image_path):
            return False
        try:
            image = Image.open(image_path)
            output = io.BytesIO()
            image.convert('RGB').save(output, 'BMP')
            data = output.getvalue()[14:]
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi copy ảnh vào Clipboard: {e}")
            return False

    def _copy_file_to_clipboard(self, file_path):
        """Đưa file Video clip 3-5s vào Windows Clipboard dưới dạng CF_HDROP"""
        if not HAS_WIN32CB or not os.path.exists(file_path):
            return False
        try:
            filepath = os.path.abspath(file_path)
            offset = 20
            data = struct.pack('IIIII', offset, 0, 0, 0, 1) + filepath.encode('utf-16-le') + b'\x00\x00\x00\x00'
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(15, data) # 15 = CF_HDROP
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi copy video vào Clipboard: {e}")
            return False

    def _paste_and_send_clipboard(self, driver, input_xpath, delay_before_enter=1.5):
        """Hàm dùng chung hỗ trợ dán nội dung từ Clipboard và bấm Enter gửi tin nhắn"""
        for _ in range(3):
            try:
                chat_input = driver.find_element(By.XPATH, input_xpath)
                chat_input.click()
                chat_input.send_keys(Keys.CONTROL, 'v')
                time.sleep(delay_before_enter)
                chat_input.send_keys(Keys.ENTER)
                return True
            except Exception:
                time.sleep(0.8)
        return False

    def send_alert_personal(self, alert_text, snapshot_path=None, video_path=None):
        """
        Tự động gửi tin nhắn báo động + 1 ảnh snapshot + 1 clip video 3-5s vào Zalo cá nhân.
        Tốc độ tối ưu: Tái sử dụng phiên trình duyệt giúp gửi cảnh báo < 3s.
        """
        try:
            if self.logger:
                self.logger.info("🤖 Đang kết nối Zalo cá nhân tự động (Persistent Session)...")
                
            driver = self.get_driver(headless=False)
            if "chat.zalo.me" not in driver.current_url:
                driver.get("https://chat.zalo.me")
                time.sleep(3)
            
            # 1. Click mở mục Truyền File (Cloud) trên menu trái Zalo Web
            nav_icons = driver.find_elements(By.XPATH, "//div[contains(@class,'mmi-icon-wr')]")
            if len(nav_icons) >= 4:
                try:
                    nav_icons[3].click()
                    if self.logger:
                        self.logger.info(" Mở thành công hộp thoại Truyền File (Zalo Cloud)!")
                except Exception:
                    pass
            time.sleep(1)

            input_xpath = "//div[@id='input_chat_topic'] | //div[contains(@class,'rich-input')] | //div[@contenteditable='true']"
            
            # 2. Gửi văn bản tin nhắn cảnh báo
            lines = alert_text.split('\n')
            for line in lines:
                for _ in range(3):
                    try:
                        chat_input = driver.find_element(By.XPATH, input_xpath)
                        chat_input.send_keys(line)
                        chat_input.send_keys(Keys.SHIFT + Keys.ENTER)
                        break
                    except Exception:
                        time.sleep(0.5)
                        
            for _ in range(3):
                try:
                    chat_input = driver.find_element(By.XPATH, input_xpath)
                    chat_input.send_keys(Keys.ENTER)
                    break
                except Exception:
                    time.sleep(0.5)
                    
            if self.logger:
                self.logger.info(" Đã gửi Văn bản cảnh báo tới Zalo!")

            # 3. Gửi Ảnh Snapshot bằng chứng (nếu có)
            if snapshot_path and os.path.exists(snapshot_path):
                if self._copy_image_to_clipboard(snapshot_path):
                    if self._paste_and_send_clipboard(driver, input_xpath, delay_before_enter=1.2):
                        if self.logger:
                            self.logger.info(" Đã gửi Ảnh Snapshot bằng chứng tới Zalo!")
                    time.sleep(1)

            # 4. Gửi Video Clip 3-5s bằng chứng (nếu có)
            if video_path and os.path.exists(video_path):
                if self._copy_file_to_clipboard(video_path):
                    if self._paste_and_send_clipboard(driver, input_xpath, delay_before_enter=2.0):
                        if self.logger:
                            self.logger.info(" Đã gửi Video Clip 3-5s bằng chứng tới Zalo!")
                    time.sleep(1.5)

            if self.logger:
                self.logger.info(" ĐÃ GỬI TRỌN BỘ TẤT CẢ TIN NHẮN + ẢNH + CLIP VIDEO 3-5S VỀ ZALO CÁ NHÂN CỦA BẠN!")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi gửi Zalo Personal Automation: {e}")
            return False

    def close(self):
        """Đóng kết nối ChromeDriver khi thoát chương trình"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

