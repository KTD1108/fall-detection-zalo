import os
import numpy as np
from ultralytics import YOLO

class YOLOPoseDetector:
    """
    Phân hệ Ước lượng Tư thế & Nhận diện Mô hình AI (YOLOv26-Pose Detector)
    - Tải mô hình YOLOv26-Pose (tự động tải trọng số pre-trained nếu chưa có).
    - Trích xuất đồng thời Bounding Box đối tượng người và 17 điểm mốc giải phẫu (COCO Keypoints).
    """
    def __init__(self, model_path="models/yolo26n-pose.pt", conf_threshold=0.45, device="auto", logger=None):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.device = device
        self.logger = logger
        
        # Đảm bảo thư mục models tồn tại
        os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else "models", exist_ok=True)
        
        if self.logger:
            self.logger.info(f"Đang khởi tạo mô hình YOLOv26-Pose từ [{self.model_path}]...")
            
        try:
            self.model = YOLO(self.model_path)
            if self.logger:
                self.logger.info(" Đã tải thành công mô hình YOLOv26-Pose AI!")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Lỗi tải YOLOv26 ({e}). Đang tự động tải mô hình mặc định 'yolo26n-pose.pt'...")
            self.model_path = "models/yolo26n-pose.pt"
            self.model = YOLO(self.model_path)


    def detect(self, frame):
        """
        Thực thi suy luận AI trên 1 khung hình.
        Args:
            frame (ndarray): Ảnh chuẩn hóa 640x640.
        Returns:
            persons (list): Danh sách các đối tượng người phát hiện được.
                            Mỗi phần tử chứa:
                            {
                                'bbox': [x1, y1, x2, y2],
                                'conf': confidence_score,
                                'keypoints': ndarray (17, 3) -> (x, y, conf)
                            }
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        persons = []
        
        if len(results) == 0 or results[0].keypoints is None:
            return persons
            
        res = results[0]
        boxes = res.boxes
        keypoints_data = res.keypoints
        
        if boxes is None or len(boxes) == 0:
            return persons
            
        # Duyệt qua các đối tượng người phát hiện
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf = float(boxes.conf[i].item())
            box = boxes.xyxy[i].cpu().numpy() # [x1, y1, x2, y2]
            
            # Lấy tên nhãn dự đoán từ mô hình (ví dụ: 'falling', 'Sitting', 'Sleeping', 'Standing', 'Walking', 'Waving Hands' hoặc 'person')
            class_name = self.model.names.get(cls_id, 'person')
            
            # Trích xuất 17 điểm mốc (x, y, conf)
            kpts = keypoints_data.data[i].cpu().numpy() # Shape: (17, 3) hoặc (17, 2)
            if kpts.shape[1] == 2:
                # Nếu thiếu cột confidence của keypoint, gắn mặc định 1.0
                conf_col = np.ones((17, 1))
                kpts = np.hstack((kpts, conf_col))
                
            persons.append({
                'bbox': box,
                'conf': conf,
                'cls_id': cls_id,
                'class_name': class_name,
                'keypoints': kpts
            })
            
        return persons

