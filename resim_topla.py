import cv2
import os

# Kalibrasyon resimlerinin kaydedileceği klasörü otomatik oluşturur
if not os.path.exists('kalibrasyon_resimleri'):
    os.makedirs('kalibrasyon_resimleri')

# 9 dikey, 6 yatay kareli tahtanın İÇ KÖŞE sayıları (9-1 = 8, 6-1 = 5)
CHECKERBOARD = (9, 6) 

cap = cv2.VideoCapture(0)
img_count = 0
MIN_IMAGES = 20

print("Kalibrasyon veri toplama başladı...")
print("Farklı açılardan (yakın, uzak, sağa sola eğik) en az 20 görüntü toplayın.")
print("'s' tuşuna basarak resmi kaydet, 'q' ile çık.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Çizgisiz, temiz ham görüntüyü arkada yedekliyoruz (Kalibrasyon için ham resim şart)
    raw_frame = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Satranç tahtası köşelerini ara
    ret_corners, corners = cv2.findChessboardCorners(
        gray,
        CHECKERBOARD,
        cv2.CALIB_CB_ADAPTIVE_THRESH +
        cv2.CALIB_CB_FAST_CHECK +
        cv2.CALIB_CB_NORMALIZE_IMAGE
    )

    # Eğer tahta bulunursa ekrana renkli çizgileri ve kayıt sayısını çiz
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
    key = cv2.waitKey(1) & 0xFF

    # 's' tuşuna basıldığında ve tahta o an kadrajda tespit edilmişse kaydet
    if key == ord('s') and ret_corners:
        cv2.imwrite(f"kalibrasyon_resimleri/img_{img_count}.jpg", raw_frame)
        print(f"Fotoğraf kalibrasyon_resimleri/img_{img_count}.jpg olarak kaydedildi!")
        img_count += 1

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()