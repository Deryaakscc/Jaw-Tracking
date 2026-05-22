import cv2
import cv2.aruco as aruco
import numpy as np

# --- 1. AYARLAR VE LOGIC ---
try:
    data = np.load('kamera_matrisi.npz')
    mtx, dist = data['mtx'], data['dist']
except:
    mtx, dist = None, None

def create_kalman():
    kalman = cv2.KalmanFilter(2, 1)
    kalman.measurementMatrix = np.array([[1, 0]], np.float32)
    kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
    kalman.processNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.005
    kalman.measurementNoiseCov = np.array([[1]], np.float32) * 0.2
    return kalman

kalman_dx, kalman_dy = create_kalman(), create_kalman()
initial_dx, initial_dy, is_calibrated, max_opening_mm = None, None, False, 0.0
MARKER_REAL_SIZE_MM = 30.0

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

while True:
    ret, frame = cap.read()
    if not ret: break
    if mtx is not None: frame = cv2.undistort(frame, mtx, dist)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None and len(ids) >= 2:
        aruco.drawDetectedMarkers(frame, corners, ids)
        id_dict = {int(ids[i][0]): corners[i][0] for i in range(len(ids))}

        if 0 in id_dict and 1 in id_dict:
            top_center = np.mean(id_dict[0], axis=0).astype(int)
            bot_center = np.mean(id_dict[1], axis=0).astype(int)
            marker_px_width = np.linalg.norm(id_dict[0][0] - id_dict[0][1])

            kalman_dx.correct(np.array([[np.float32(bot_center[0] - top_center[0])]]))
            kalman_dy.correct(np.array([[np.float32(bot_center[1] - top_center[1])]]))
            f_dx, f_dy = kalman_dx.predict()[0][0], kalman_dy.predict()[0][0]
            mm_per_px = MARKER_REAL_SIZE_MM / marker_px_width

            if is_calibrated:
                current_opening_mm = max(0, (f_dy - initial_dy) * mm_per_px)
                status = "ACIK" if current_opening_mm > 3.0 else "KAPALI"

                if status == "KAPALI":
                    current_opening_mm, lateral_deviation_mm, initial_dx = 0.0, 0.0, f_dx
                else:
                    lateral_deviation_mm = (f_dx - initial_dx) * mm_per_px

                if current_opening_mm > max_opening_mm: max_opening_mm = current_opening_mm

                # --- 🎛️ SADELEŞTİRİLMİŞ UI PANEL ---
                cv2.rectangle(frame, (15, 15), (320, 150), (40, 40, 40), cv2.FILLED)
                cv2.rectangle(frame, (15, 15), (320, 150), (200, 200, 200), 2)
                cv2.line(frame, tuple(top_center), tuple(bot_center), (255, 0, 0), 2)

                side = "SAGA" if lateral_deviation_mm > 0 else "SOLA"
                kayma_txt = f"KAYMA: {abs(lateral_deviation_mm):.1f} mm {side}" if abs(lateral_deviation_mm) > 1.5 else "KAYMA: Dengeli"
                
                texts = [f"DURUM: {status}", f"Anlik Aciklik: {current_opening_mm:.1f} mm", f"MAX ACIKLIK: {max_opening_mm:.1f} mm", kayma_txt]
                colors = [(0, 0, 255) if status == "ACIK" else (0, 255, 0), (255, 255, 255), (0, 165, 255), (0, 0, 255) if "SAGA" in kayma_txt or "SOLA" in kayma_txt else (255, 255, 255)]

                for idx, (txt, col) in enumerate(zip(texts, colors)):
                    cv2.putText(frame, txt, (30, 45 + idx * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6 if idx != 0 else 0.7, col, 1 if idx != 0 else 2)
            else:
                cv2.rectangle(frame, (15, 15), (420, 65), (0, 0, 0), cv2.FILLED)
                cv2.putText(frame, "Agzinizi Kapatip 'c' Tusuna Basin", (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    cv2.imshow("Hassas Klinik Cene Takip Sistemi", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('c') and 'top_center' in locals():
        initial_dx, initial_dy, max_opening_mm, is_calibrated = f_dx, f_dy, 0.0, True
    if key == ord('r'): max_opening_mm = 0.0
    if key == ord('q'): break

cap.release()
cv2.destroyAllWindows()