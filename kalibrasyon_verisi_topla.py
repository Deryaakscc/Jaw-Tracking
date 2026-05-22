import cv2
import os

if not os.path.exists('kalibrasyon_resimleri'):
    os.makedirs('kalibrasyon_resimleri')


CHECKERBOARD = (8, 5) 

cap = cv2.VideoCapture(0)
img_count = 0
MIN_IMAGES = 20

print("Kalibrasyon başlıyor...")
print("Farklı açılardan (yakın, uzak, eğik) en az 20 görüntü topla.")
print("'s' tuşuna basarak kaydet, 'q' ile çık.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

   
    raw_frame = frame.copy()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    ret_corners, corners = cv2.findChessboardCorners(
        gray,
        CHECKERBOARD,
        cv2.CALIB_CB_ADAPTIVE_THRESH +
        cv2.CALIB_CB_FAST_CHECK +
        cv2.CALIB_CB_NORMALIZE_IMAGE
    )

    if ret_corners:
        cv2.drawChessboardCorners(frame, CHECKERBOARD, corners, ret_corners)
        cv2.putText(frame, f"IMG: {img_count}/{MIN_IMAGES}",
                    (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "Chessboard bulunamadi",
                    (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 255), 2)

    cv2.imshow("Calibration Data Collection", frame)

    key = cv2.waitKey(1) & 0xFF # Daha güvenli tuş okuma

    if key == ord('s') and ret_corners:
        # ÖNEMLİ: Çizgisiz, temiz görüntüyü kaydediyoruz
        cv2.imwrite(f"kalibrasyon_resimleri/img_{img_count}.jpg", raw_frame)
        img_count += 1
        print(f"Fotoğraf {img_count} kaydedildi!")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()