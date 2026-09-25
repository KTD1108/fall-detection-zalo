import os
import sys
import time
import yaml
import cv2
import numpy as np

# Thêm đường dẫn src vào system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from logger import SystemLogger
from camera import CameraStream
from detector import YOLOPoseDetector
from fall_analyzer import RealtimeFallAnalyzer
from zalo_notifier import ZaloNotifier

# Các đường nối 17 khớp xương chuẩn COCO
COCO_SKELETON_EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 4),             # Đầu/mặt
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),     # Tay
    (5, 11), (6, 12), (11, 12),                 # Thân người
    (11, 13), (13, 15), (12, 14), (14, 16)      # Chân
]

def load_config(config_path="config/config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình [{config_path}]")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def draw_skeleton(frame, keypoints, bbox, label="Normal", confidence=0.0):
    """
    Vẽ trực quan khung xương 17 điểm mốc (Skeleton), Khung bao (BBox) và Nhãn nhịp vận hành lên màn hình UI.
    """
    x1, y1, x2, y2 = map(int, bbox)
    
    # Quyết định màu sắc theo nhãn
    if label == "Falling":
        color = (0, 0, 255) # Đỏ rực khi ngã
    elif label == "Bending":
        color = (0, 255, 255) # Vàng khi cúi người
    elif label == "Sitting":
        color = (255, 200, 0) # Xanh lam nhạt khi ngồi bệt
    else:
        color = (0, 255, 0) # Xanh lá khi bình thường
        
    # 1. Vẽ Khung bao đối tượng (Bounding Box)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # 2. Vẽ các đường nối khớp xương (Skeleton Edges)
    for p1_idx, p2_idx in COCO_SKELETON_EDGES:
        pt1 = keypoints[p1_idx]
        pt2 = keypoints[p2_idx]
        if pt1[2] > 0.3 and pt2[2] > 0.3:
            pos1 = (int(pt1[0]), int(pt1[1]))
            pos2 = (int(pt2[0]), int(pt2[1]))
            cv2.line(frame, pos1, pos2, (255, 255, 255), 2)
            
    # 3. Vẽ 17 điểm mốc khớp xương (Keypoint Nodes)
    for idx, pt in enumerate(keypoints):
        if pt[2] > 0.3:
            pos = (int(pt[0]), int(pt[1]))
            cv2.circle(frame, pos, 4, color, -1)
            
    # 4. Hiển thị nhãn phân loại và độ tin cậy
    label_text = f"{label} ({confidence:.2f})"
    cv2.putText(frame, label_text, (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def main():
    print("=" * 70)
    print(" HỆ THỐNG PHÁT HIỆN TÉ NGÃ NGƯỜI CAO TUỔI (YOLO26-POSE + ZALO API)")
    print("=" * 70)
    
    # 1. Tải cấu hình & Khởi tạo Logger
    cfg = load_config()
    logger = SystemLogger(log_file_path=cfg['outputs']['log_file'])
    logger.info("Đang khởi động hệ thống phát hiện té ngã...")
    
    # 2. Khởi tạo các phân hệ mô-đun
    camera = CameraStream(
        source=cfg['camera']['source'],
        target_fps=cfg['camera']['target_fps'],
        input_width=cfg['camera']['input_width'],
        input_height=cfg['camera']['input_height'],
        buffer_seconds=cfg['outputs']['buffer_duration_seconds'],
        logger=logger
    )
    
    detector = YOLOPoseDetector(
        model_path=cfg['model']['path'],
        conf_threshold=cfg['model']['confidence_threshold'],
        device=cfg['model']['device'],
        logger=logger
    )
    
    analyzer = RealtimeFallAnalyzer(
        vertical_velocity_threshold=cfg['fall_detection']['vertical_velocity_threshold'],
        bbox_aspect_ratio_threshold=cfg['fall_detection']['bbox_aspect_ratio_threshold'],
        body_inclination_threshold=cfg['fall_detection']['body_inclination_threshold'],
        consecutive_frames_trigger=cfg['fall_detection']['consecutive_frames_trigger'],
        cooldown_seconds=cfg['fall_detection']['cooldown_seconds'],
        logger=logger
    )
    
    notifier = ZaloNotifier(config_path="config/zalo_config.json", logger=logger)
    
    logger.info("Hệ thống đã sẵn sàng! Nhấn 'q' để thoát, nhấn 'f' để giả lập sự cố ngã.")
    
    # 3. Vòng lặp giám sát thời gian thực
    fps_counter = 0
    start_time = time.time()
    current_fps = 0.0
    
    alert_banner_until = 0 # Quản lý thời gian hiển thị banner cảnh báo đỏ trên màn hình GUI
    
    while True:
        loop_start = time.time()
        ret, frame, raw_frame = camera.read()
        
        if not ret or frame is None:
            logger.warning("Không nhận được luồng hình ảnh từ camera. Đang kết thúc...")
            break
            
        fps_counter += 1
        if (time.time() - start_time) >= 1.0:
            current_fps = fps_counter / (time.time() - start_time)
            fps_counter = 0
            start_time = time.time()
            
        # Suy luận YOLO26-Pose nhận diện người & 17 keypoints
        persons = detector.detect(frame)
        
        current_label = "Normal"
        current_conf = 0.0
        
        for person in persons:
            label, conf, is_fall_alert, metrics = analyzer.analyze(person, frame.shape[0], frame.shape[1])
            current_label = label
            current_conf = conf
            
            # Vẽ bộ khung xương & bounding box
            draw_skeleton(frame, person['keypoints'], person['bbox'], label=label, confidence=conf)
            
            # KÍCH HOẠT CẢNH BÁO KHẨN CẤP KHI NGA
            if is_fall_alert:
                alert_banner_until = time.time() + 4.0 # Hiển thị màn hình đỏ trong 4s
                
                # Trích xuất 1 ảnh snapshot + 1 clip 3-5s từ bộ đệm xoay vòng
                snapshot_path, video_path = camera.export_evidence_clip(
                    output_dir=cfg['outputs']['output_dir'],
                    prefix="fall_evidence"
                )
                
                # Gửi cảnh báo khẩn cấp qua Zalo API / Mock Mode
                notifier.send_alert(snapshot_path, video_path, metrics)
                
        # Giả lập sự cố ngã bằng phím tắt 'f' (nếu cấu hình debug bật)
        key = cv2.waitKey(1) & 0xFF
        enable_manual_trigger = cfg.get('debug', {}).get('enable_manual_trigger', False)
        if enable_manual_trigger and key == ord('f'):
            logger.warning("⌨️ [DEBUG] Người dùng nhấn phím 'f' - Giả lập sự cố ngã khẩn cấp!")
            alert_banner_until = time.time() + 4.0
            snapshot_path, video_path = camera.export_evidence_clip(
                output_dir=cfg['outputs']['output_dir'],
                prefix="manual_test_fall"
            )
            notifier.send_alert(snapshot_path, video_path)
        elif key == ord('q') or key == 27: # 'q' hoặc ESC để thoát
            break
            
        # Hiển thị thông tin hệ thống lên màn hình GUI (Banner Header)
        latency_ms = (time.time() - loop_start) * 1000
        
        # Thanh tiêu đề trạng thái
        cv2.rectangle(frame, (0, 0), (640, 40), (40, 40, 40), -1)
        info_text = f"FPS: {current_fps:.1f} | Latency: {latency_ms:.1f}ms | Status: {current_label} ({current_conf:.2f})"
        cv2.putText(frame, info_text, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
        
        # Nếu đang trong thời gian cảnh báo ngã -> Hiển thị Màn hình Cảnh báo Đỏ (Red Alert Banner)
        if time.time() < alert_banner_until:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (640, 640), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
            cv2.putText(frame, "⚠️ FALL DETECTED! SENDING ZALO ALERT...", (30, 320),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 3)

        # Hiển thị cửa sổ OpenCV GUI
        cv2.imshow("Fall Detection System - YOLO26-Pose + Zalo Alert", frame)

    # Giải phóng tài nguyên khi thoát
    camera.release()
    cv2.destroyAllWindows()
    logger.info("Đã tắt hệ thống an toàn.")

if __name__ == '__main__':
    main()

