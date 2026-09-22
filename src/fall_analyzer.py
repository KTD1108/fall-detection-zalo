import math
import time
import numpy as np

class RealtimeFallAnalyzer:
    """
    Phân hệ Lập luận Thời gian thực & Kháng Báo động giả (Fall Analyzer Module)
    - Phân tích biến thiên 17 điểm mốc (COCO Keypoints) và Khung bao (Bounding Box) theo chuỗi thời gian.
    - Phân biệt sự cố té ngã thực tế (`Falling`) với các cử chỉ hạ thấp trọng tâm đặc thù của người Việt:
      + `Bending`: Cúi người nhặt đồ, thắp hương/cầu nguyện.
      + `Sitting`: Ngồi bệt ăn cơm, ngồi xổm.
      + `Lying`: Nằm nghỉ trên chiếu/sàn.
      + `Normal`: Đi lại, đứng sinh hoạt bình thường.
    """
    def __init__(self,
                 vertical_velocity_threshold=0.12,
                 bbox_aspect_ratio_threshold=1.15,
                 body_inclination_threshold=45.0,
                 consecutive_frames_trigger=4,
                 cooldown_seconds=10,
                 logger=None):
        
        self.v_threshold = vertical_velocity_threshold
        self.ratio_threshold = bbox_aspect_ratio_threshold
        self.angle_threshold = body_inclination_threshold
        self.trigger_frames = consecutive_frames_trigger
        self.cooldown_seconds = cooldown_seconds
        self.logger = logger
        
        # Lịch sử vị trí điểm mốc hông (Hip Y-coordinate history)
        self.hip_y_history = []
        self.max_history = 10
        
        # Bộ đếm khung hình té ngã liên tiếp (Consecutive fall counter)
        self.fall_counter = 0
        self.last_alert_time = 0

    def _get_center(self, kpts, idx1, idx2):
        """Tính trung điểm giữa 2 keypoints (ví dụ: trung điểm 2 vai hoặc 2 hông)"""
        p1, p2 = kpts[idx1], kpts[idx2]
        if p1[2] > 0.2 and p2[2] > 0.2:
            return (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
        elif p1[2] > 0.2:
            return p1[0], p1[1]
        elif p2[2] > 0.2:
            return p2[0], p2[1]
        return None, None

    def _calculate_body_inclination(self, shoulder_center, hip_center):
        """
        Tính góc nghiêng của thân người (Torso Inclination Angle) so with phương thẳng đứng (Trục Y).
        Góc = 0° (đứng thẳng), góc ~ 90° (nằm ngang).
        """
        if shoulder_center[0] is None or hip_center[0] is None:
            return 0.0
            
        dx = shoulder_center[0] - hip_center[0]
        dy = shoulder_center[1] - hip_center[1] # Trục Y hướng xuống dưới trong OpenCV
        
        # Độ dài đoạn thân người
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            return 0.0
            
        # Tính góc so với phương đứng (dy / dist)
        cos_theta = abs(dy) / dist
        cos_theta = max(-1.0, min(1.0, cos_theta))
        angle_rad = math.acos(cos_theta)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg

    def analyze(self, person_data, frame_height=640, frame_width=640):
        """
        Phân tích đối tượng người trên khung hình hiện tại.
        Args:
            person_data (dict): Đối tượng người chứa 'bbox' và 'keypoints' (17, 3).
        Returns:
            label (str): Nhãn phân loại ('Falling', 'Bending', 'Sitting', 'Lying', 'Normal').
            confidence (float): Độ tin cậy của dự đoán (0.0 - 1.0).
            is_fall_alert (bool): True nếu phát hiện sự cố ngã khẩn cấp vượt ngưỡng.
            metrics (dict): Các thông số tính toán (V_y, AspectRatio, Angle).
        """
        if person_data is None:
            return "Normal", 0.0, False, {}
            
        bbox = person_data['bbox'] # [x1, y1, x2, y2]
        kpts = person_data['keypoints'] # (17, 3)
        
        x1, y1, x2, y2 = bbox
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        aspect_ratio = float(w) / float(h) # Width / Height
        
        # 1. Trích xuất vị trí vai và hông
        # COCO: 5=Left Shoulder, 6=Right Shoulder, 11=Left Hip, 12=Right Hip
        sh_x, sh_y = self._get_center(kpts, 5, 6)
        hip_x, hip_y = self._get_center(kpts, 11, 12)
        
        if hip_y is None:
            hip_y = (y1 + y2) / 2.0
        if sh_y is None:
            sh_y = y1
            
        # 2. Tính vận tốc dịch chuyển trục đứng Vy (Normalized vertical velocity)
        self.hip_y_history.append(hip_y / float(frame_height))
        if len(self.hip_y_history) > self.max_history:
            self.hip_y_history.pop(0)
            
        v_y = 0.0
        if len(self.hip_y_history) >= 2:
            # Tốc độ giảm chiều cao (tốc độ rơi)
            v_y = (self.hip_y_history[-1] - self.hip_y_history[0]) / float(len(self.hip_y_history) - 1)
            
        # 3. Tính góc nghiêng thân người (Body Inclination Angle)
        body_angle = self._calculate_body_inclination((sh_x, sh_y), (hip_x, hip_y))
        
        # 4. Phân loại tư thế (Classification Logic kết hợp AI Model + Time-series Logic)
        model_class_name = person_data.get('class_name', '').lower()
        model_conf = person_data.get('conf', 0.85)
        
        label = person_data.get('class_name', 'Normal')
        confidence = model_conf
        
        is_sudden_drop = v_y > self.v_threshold
        is_horizontal = aspect_ratio > self.ratio_threshold
        is_inclined = body_angle > self.angle_threshold
        
        # --- BỘ LỌC KHÁNG BÁO ĐỘNG GIẢ & KẾT HỢP DỰ ĐOÁN AI ---
        if model_class_name == 'falling' or (is_sudden_drop and (is_horizontal or is_inclined)):
            # Mô hình AI báo 'falling' HOẶC cú hạ thấp trọng tâm ĐỘT NGỘT + NẰM NGANG/NGHIÊNG NẶNG -> TÉ NGÃ
            label = "Falling"
            confidence = max(model_conf, min(0.99, 0.75 + v_y * 2.0))
        elif is_inclined and not is_sudden_drop:
            if aspect_ratio < 1.0 and (hip_y / frame_height) < 0.75:
                # Thân người nghiêng nhưng di chuyển CHẬM + Hông vẫn ở trên cao -> CÚI NGƯỜI (Bending)
                label = "Bending"
                confidence = 0.90
            elif (hip_y / frame_height) >= 0.75 and aspect_ratio < 1.2:
                label = "Sitting" if model_class_name != 'sleeping' else "Sleeping"
                confidence = max(model_conf, 0.88)
            elif is_horizontal:
                label = "Sleeping"
                confidence = max(model_conf, 0.85)
        elif is_horizontal and not is_sudden_drop:
            if model_class_name != 'falling':
                label = "Sleeping"
                confidence = max(model_conf, 0.82)

            
        # 5. Xử lý bộ đếm kích hoạt cảnh báo té ngã (Trigger Accumulator & Cooldown)
        current_time = time.time()
        in_cooldown = (current_time - self.last_alert_time) < self.cooldown_seconds
        
        is_fall_alert = False
        if label == "Falling":
            self.fall_counter += 1
            if self.fall_counter >= self.trigger_frames and not in_cooldown:
                is_fall_alert = True
                self.last_alert_time = current_time
                self.fall_counter = 0 # Reset bộ đếm
                if self.logger:
                    self.logger.alert(f"Phát hiện sự cố ngã khẩn cấp! (Confidence: {confidence:.2f}, Vy: {v_y:.3f}, AspectRatio: {aspect_ratio:.2f}, Angle: {body_angle:.1f}°)")
        else:
            self.fall_counter = max(0, self.fall_counter - 1)
            
        metrics = {
            'v_y': v_y,
            'aspect_ratio': aspect_ratio,
            'body_angle': body_angle,
            'fall_counter': self.fall_counter
        }
        
        return label, confidence, is_fall_alert, metrics
