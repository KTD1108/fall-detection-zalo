import cv2
import time
import os
from collections import deque

class CameraStream:
    """
    Phân hệ Thu nhận & Tiền xử lý Luồng Video (Camera Module)
    - Quản lý giao tiếp Webcam / Video file với tốc độ 24-30 FPS.
    - Tiền xử lý chuẩn hóa khung hình về 640x640 pixels.
    - Duy trì Bộ đệm khung hình tròn (Circular Frame Buffer) lưu lại 3-5 giây video liên tục
      trước và sau khi sự cố ngã xảy ra.
    """
    def __init__(self, source=0, target_fps=30, input_width=640, input_height=640, buffer_seconds=4, logger=None):
        self.source = source
        self.target_fps = target_fps
        self.input_width = input_width
        self.input_height = input_height
        self.logger = logger
        
        # Mở camera hoặc file video
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            if self.logger:
                self.logger.error(f"Không thể mở nguồn video/camera: {self.source}")
            raise RuntimeError(f"Cannot open camera/video source: {self.source}")
            
        # Thử lấy FPS của camera thực tế
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = actual_fps if actual_fps > 0 else self.target_fps
        
        # Bộ đệm chứa các khung hình vừa trôi qua (Circular Buffer)
        self.buffer_capacity = int(self.fps * buffer_seconds)
        self.frame_buffer = deque(maxlen=self.buffer_capacity)
        
        if self.logger:
            self.logger.info(f"Đã mở thành công nguồn camera {self.source} | FPS: {self.fps} | Khả năng bộ đệm: {self.buffer_capacity} khung hình ({buffer_seconds}s)")

    def read(self):
        """
        Đọc 1 khung hình từ luồng video, chuẩn hóa và lưu vào bộ đệm.
        Returns:
            ret (bool): Trạng thái đọc thành công hay không.
            frame_resized (ndarray): Khung hình đã chuẩn hóa 640x640 pixels.
            raw_frame (ndarray): Khung hình gốc từ camera.
        """
        ret, raw_frame = self.cap.read()
        if not ret or raw_frame is None:
            return False, None, None
            
        # Chuẩn hóa về 640x640
        frame_resized = cv2.resize(raw_frame, (self.input_width, self.input_height))
        
        # Đưa vào bộ đệm xoay vòng kèm Timestamp
        timestamp = time.time()
        self.frame_buffer.append((timestamp, frame_resized.copy()))
        
        return True, frame_resized, raw_frame

    def export_evidence_clip(self, output_dir="data/outputs", prefix="fall_evidence"):
        """
        Trích xuất 1 ảnh snapshot khẩn cấp và 1 video clip 3-5 giây từ bộ đệm khung hình.
        Returns:
            snapshot_path (str): Đường dẫn ảnh sự cố (.jpg).
            video_path (str): Đường dẫn video clip sự cố (.mp4).
        """
        os.makedirs(output_dir, exist_ok=True)
        time_str = time.strftime("%Y%m%d_%H%M%S")
        
        snapshot_filename = f"{prefix}_{time_str}.jpg"
        video_filename = f"{prefix}_{time_str}.mp4"
        
        snapshot_path = os.path.join(output_dir, snapshot_filename)
        video_path = os.path.join(output_dir, video_filename)
        
        if len(self.frame_buffer) == 0:
            return None, None
            
        # 1. Lưu ảnh snapshot của khung hình gần nhất
        latest_timestamp, latest_frame = self.frame_buffer[-1]
        cv2.imwrite(snapshot_path, latest_frame)
        
        # 2. Đóng gói video clip từ toàn bộ bộ đệm khung hình (Có fallback Codec)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_video = cv2.VideoWriter(video_path, fourcc, int(self.fps), (self.input_width, self.input_height))
        
        if not out_video.isOpened():
            # Fallback sang XVID (.avi) nếu mp4v thất bại
            video_path = video_path.replace('.mp4', '.avi')
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out_video = cv2.VideoWriter(video_path, fourcc, int(self.fps), (self.input_width, self.input_height))
            
        if out_video.isOpened():
            for _, frame in list(self.frame_buffer):
                out_video.write(frame)
            out_video.release()
        else:
            if self.logger:
                self.logger.warning("Không thể mở VideoWriter để lưu clip sự cố.")
            video_path = None


        
        if self.logger:
            self.logger.info(f"Đã trích xuất bằng chứng sự cố: Ảnh [{snapshot_path}], Video [{video_path}]")
            
        return snapshot_path, video_path

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            if self.logger:
                self.logger.info("Đã đóng kết nối camera.")
