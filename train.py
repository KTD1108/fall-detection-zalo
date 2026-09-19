import os
from ultralytics import YOLO

def train_custom_model(data_yaml="data/dataset.yaml", epochs=100, batch_size=8, imgsz=640):
    """
    Script Huấn Luyện & Tinh Chỉnh Mô Hình YOLOv11-Pose (Fine-Tuning Script)
    Bám sát các siêu tham số huấn luyện tại Mục 2.3.3 trong Bài Báo Cáo PDF:
    - Learning Rate (lr0) = 0.001
    - Batch Size = 8
    - Epochs = 100
    - Momentum = 0.937
    - Weight Decay = 0.0005
    - Kích thước ảnh đầu vào: 640x640 pixels
    - Tỷ lệ dữ liệu đề xuất: 70% Train / 20% Val / 10% Test
    """
    print("=" * 70)
    print(" BẮT ĐẦU HUẤN LUYỆN TINH CHỈNH MÔ HÌNH YOLOV11-POSE CUSTOM DATASET")
    print("=" * 70)
    
    if not os.path.exists(data_yaml):
        print(f"⚠️ Chưa tìm thấy file cấu hình tập dữ liệu [{data_yaml}].")
        print("💡 Hướng dẫn: Bạn tạo file data/dataset.yaml chứa đường dẫn thư mục ảnh train/val theo chuẩn YOLO Keypoints.")
        return
        
    # 1. Tải trọng số khởi tạo YOLOv11-Pose pre-trained
    base_model_path = "models/yolo11n-pose.pt"
    if not os.path.exists(base_model_path):
        base_model_path = "yolo11n-pose.pt"
        
    model = YOLO(base_model_path)
    
    # 2. Thực thi quá trình huấn luyện (Training Loop)
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        lr0=0.001,
        momentum=0.937,
        weight_decay=0.0005,
        project="models/runs",
        name="yolo11_fall_custom",
        device="auto"
    )
    
    print("\n HUẤN LUYỆN HOÀN TẤT!")
    print(f"Trọng số tốt nhất (Best Weights) được lưu tại: models/runs/yolo11_fall_custom/weights/best.pt")

if __name__ == '__main__':
    train_custom_model()
