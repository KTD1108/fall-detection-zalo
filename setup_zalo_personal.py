import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from zalo_personal_automation import ZaloPersonalAutomation

if __name__ == '__main__':
    zalo_auto = ZaloPersonalAutomation(profile_dir="zalo_browser_profile", target_chat="Truyền File")
    zalo_auto.setup_login()
