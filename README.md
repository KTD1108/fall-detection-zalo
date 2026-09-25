# 🚨 HỆ THỐNG PHÁT HIỆN TÉ NGÃ NGƯỜI CAO TUỔI TẠI GIA ĐÌNH (YOLOv11-Pose + Zalo Alert)

Hệ thống giám sát an toàn thụ động theo thời gian thực (Real-time Passive Monitoring System), tự động phát hiện sự cố té ngã ở người cao tuổi bằng AI (YOLOv11-Pose) và gửi cảnh báo khẩn cấp (kèm 1 Ảnh Snapshot + 1 Clip Video 3–5 giây bằng chứng) trực tiếp về ứng dụng **Zalo cá nhân** của người chăm sóc.

---

## 🌟 ĐẶC ĐIỂM NỔI BẬT

- **AI Nhận Diện Thời Gian Thực**: Sử dụng mô hình Deep Learning **YOLOv11-Pose** trích xuất 17 điểm mốc khớp xương (COCO Keypoints) đạt tốc độ $\ge 25$ FPS.
- **Thuật Toán Kháng Báo Động Giả (False Alarm Prevention)**: Phân biệt chính xác té ngã thực tế với các sinh hoạt hạ thấp trọng tâm đặc thù của người Việt (ngồi bệt ăn cơm, nằm chiếu, cúi người nhặt đồ, thắp hương).
- **Cảnh Báo Zalo Cá Nhân Tự Động**: Gửi tin nhắn cảnh báo + Ảnh bằng chứng + Clip video 3-5s qua Zalo Web Automation mà **không cần đăng ký Zalo Official Account (OA) Doanh Nghiệp**.
- **Còi Báo Động Tại Chỗ**: Loa máy tính phát tiếng còi cảnh báo tần số cao ngay khi phát hiện sự cố.
- **Độ Trễ Khẩn Cấp Thấp**: Thời gian từ khi ngã đến khi Zalo phát thông báo $< 3$ giây.

---

## 🛠️ YÊU CẦU MÔI TRƯỜNG

- **Hệ điều hành**: Windows 10 / 11 hoặc Linux / macOS.
- **Python**: Phiên bản `3.9` hoặc `3.10` (Khuyên dùng `3.10`).
- **Phần cứng**: Máy tính có Webcam (hoặc Webcam USB) và kết nối Internet.

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT VÀ VẬN HÀNH

### Bước 1: Tải mã nguồn (Clone Repository)
Mở Terminal / Command Prompt và chạy lệnh:
```bash
git clone https://github.com/KTD1108/fall-detection-zalo.git
cd fall-detection-zalo
```

### Bước 2: Tạo môi trường ảo (Khuyên dùng)
```bash
# Trên Windows PowerShell / CMD
python -m venv venv
venv\Scripts\activate

# Trên Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 4: Tải mô hình AI (QUAN TRỌNG)
Vì lý do bảo mật và dung lượng, các file `.pt` (trọng số mô hình) không được đẩy lên GitHub. 
- Hãy chép file model YOLOv11-Pose đã train của team (`best.pt` có 6 lớp phân loại: Sitting, Sleeping, Standing, Walking, Waving Hands, falling) vào thư mục `models/` của dự án.
- Nếu không có file này, hệ thống sẽ tự động tải model mặc định của thư viện (`yolo11n-pose.pt` - chỉ nhận diện được lớp `person`, dẫn đến phân loại tư thế sai).


---

## 📲 CẤU HÌNH ZALO VÀ ĐĂNG NHẬP LẦN ĐẦU

### 1. Tạo file cấu hình Zalo
Copy file cấu hình mẫu `zalo_config.json.example` thành `zalo_config.json`:
```bash
# Trên Windows
copy config\zalo_config.json.example config\zalo_config.json

# Trên Linux / macOS
cp config/zalo_config.json.example config/zalo_config.json
```

*(Mặc định thông báo sẽ gửi vào mục **Truyền File / Cloud** của chính bạn trên Zalo. Nếu muốn gửi cho tài khoản Zalo khác, mở file `config/zalo_config.json` và sửa `"receiver_phone_id": "Tên_Zalo_Người_Nhận"`).*

### 2. Đăng nhập Zalo Web (Quét mã QR lần đầu duy nhất)
Chạy script thiết lập kết nối:
```bash
python setup_zalo_personal.py
```
- Trình duyệt Chrome sẽ mở trang `chat.zalo.me`.
- Dùng app Zalo trên điện thoại quét mã QR để đăng nhập.
- Phiên đăng nhập sẽ được lưu vĩnh viễn trên máy của bạn (không bao giờ phải quét lại).

---

## 🖥️ CHẠY HỆ THỐNG GIÁM SÁT

Chạy ứng dụng chính:
```bash
python main.py
```

- Màn hình camera sẽ hiển thị khung xương 17 khớp và nhãn trạng thái (`Normal`, `Bending`, `Sitting`, `Falling`).
- **Thử nghiệm giả lập ngã khẩn cấp**: Nhấn phím **`f`** trên bàn phím để giả lập một cú ngã test.
- **Thoát chương trình**: Nhấn phím **`q`** hoặc **`Esc`**.

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
fall-detection-zalo
│
├── config
│   ├── config.yaml              # Cấu hình Camera, ngưỡng vận tốc ngã Vy, góc nghiêng
│   ├── zalo_config.json.example # File cấu hình Zalo mẫu
│   └── zalo_config.json         # File cấu hình Zalo thực tế (Đã được .gitignore bảo mật)
│
├── data
│   ├── raw                     # Video / ảnh thử nghiệm
│   └── outputs                 # Thư mục lưu ảnh Snapshot và clip Video sự cố ngã
│
├── models
│   └── best.pt                 # Trọng số mô hình AI YOLOv11-Pose
│
├── src
│   ├── camera.py               # Quản lý luồng Webcam & Bộ đệm xoay vòng 3-5s
│   ├── detector.py             # Trích xuất 17 điểm mốc (YOLOv11-Pose)
│   ├── fall_analyzer.py        # Thuật toán thời gian thực & kháng báo động giả
│   ├── zalo_notifier.py        # Phân hệ cảnh báo Zalo
│   └── zalo_personal_automation.py # Tự động hóa gửi tin nhắn + ảnh + video qua Zalo Web
│
├── logs
│   └── system_events.log       # Nhật ký sự kiện hệ thống
│
├── setup_zalo_personal.py       # Script quét mã QR đăng nhập Zalo lần đầu
├── main.py                     # Luồng chính thực thi ứng dụng & Giao diện GUI
└── requirements.txt            # Thư viện phụ thuộc
```

---

## ❓ CÂU HỎI THƯỜNG GẶP (TROUBLESHOOTING)

1. **Không mở được Webcam?**
   - Mở file `config/config.yaml`, sửa `camera: source: 0` thành `1` hoặc `2` tùy theo cổng webcam của máy tính.
2. **Đẩy code lên GitHub có bị lộ tài khoản Zalo không?**
   - **Không.** Thư mục `zalo_browser_profile/` chứa phiên đăng nhập Zalo và file `config/zalo_config.json` đã được đưa vào `.gitignore` để bảo mật tuyệt đối.
