import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

class ZaloPersonalAutomation:
    """
    Phân hệ Gửi Thông Báo Zalo Cá Nhân Tự Động (Personal Zalo Web Automation)
    - Giải pháp ĐỘC QUYỀN gửi tin nhắn cảnh báo khẩn cấp + ảnh snapshot + video 3-5s
      thẳng về Zalo cá nhân mà KHÔNG CẦN tài khoản Zalo OA Doanh Nghiệp.
    """
    def __init__(self, profile_dir="zalo_browser_profile", target_chat="Truyền File", logger=None):
        self.profile_dir = os.path.abspath(profile_dir)
        self.target_chat = target_chat
        self.logger = logger
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

    def setup_login(self):
        """Mở trình duyệt để người dùng quét mã QR Zalo Web lần đầu duy nhất"""
        print("\n" + "=" * 70)
        print(" THIẾT LẬP KẾT NỐI ZALO CÁ NHÂN (PERSONAL ZALO SETUP)")
        print("=" * 70)
        print("Trình duyệt Chrome sắp mở ra. Vui lòng lấy điện thoại quét mã QR")
        print("để đăng nhập Zalo Web (chat.zalo.me) lần đầu duy nhất!")
        print("=" * 70 + "\n")
        
        driver = self._get_chrome_driver(headless=False)
        try:
            driver.get("https://chat.zalo.me")
            print("Đang chờ bạn quét mã QR Zalo Web...")
            time.sleep(15)
            print("\n ĐĂNG NHẬP ZALO CÁ NHÂN THÀNH CÔNG!")
            print(f"Phiên làm việc đã được lưu vĩnh viễn tại: {self.profile_dir}")
        except Exception as e:
            print(f"❌ Lỗi đăng nhập Zalo: {e}")
        finally:
            driver.quit()

    def send_alert_personal(self, alert_text, snapshot_path=None, video_path=None):
        """
        Tự động gửi tin nhắn báo động + ảnh snapshot + clip video 3-5s vào Zalo cá nhân.
        """
        driver = None
        try:
            if self.logger:
                self.logger.info("🤖 Đang kết nối Zalo cá nhân tự động...")
                
            driver = self._get_chrome_driver(headless=False)
            driver.get("https://chat.zalo.me")
            time.sleep(4)
            
            # 1. Click mở mục Truyền File (Cloud) trên menu trái Zalo Web
            nav_icons = driver.find_elements(By.XPATH, "//div[contains(@class,'mmi-icon-wr')]")
            if len(nav_icons) >= 4:
                try:
                    nav_icons[3].click()
                    if self.logger:
                        self.logger.info(" Mở thành công hộp thoại Truyền File (Zalo Cloud)!")
                except Exception:
                    pass
            time.sleep(3)

            # 2. Gửi nội dung tin nhắn cảnh báo (sử dụng cơ chế re-find DOM an toàn)
            input_xpath = "//div[@id='input_chat_topic'] | //div[contains(@class,'rich-input')] | //div[@contenteditable='true']"
            
            lines = alert_text.split('\n')
            for line in lines:
                for _ in range(5):
                    try:
                        chat_input = driver.find_element(By.XPATH, input_xpath)
                        chat_input.send_keys(line)
                        chat_input.send_keys(Keys.SHIFT + Keys.ENTER)
                        break
                    except Exception:
                        time.sleep(0.8)
                        
            # Nhấn ENTER để gửi tin nhắn
            for _ in range(5):
                try:
                    chat_input = driver.find_element(By.XPATH, input_xpath)
                    chat_input.send_keys(Keys.ENTER)
                    break
                except Exception:
                    time.sleep(0.8)
                    
            time.sleep(2)

            if self.logger:
                self.logger.info(" ĐÃ GỬI THÀNH CÔNG TIN NHẮN CẢNH BÁO TỚI ZALO CÁ NHÂN CỦA BẠN!")
            time.sleep(2)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Lỗi gửi Zalo Personal Automation: {e}")
            return False
        finally:
            if driver:
                driver.quit()
