import cv2
import numpy as np
import glob


CHECKERBOARD = (8, 5) 
SQUARE_SIZE = 30  # mm (karenin bir kenarı)


criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints = [] # 3D noktalar (gerçek dünya)
imgpoints = [] # 2D noktalar (fotoğraftaki pikseller)


images = glob.glob('kalibrasyon_resimleri/*.jpg')
print(f"{len(images)} görüntü bulundu, işleniyor...")

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD)

    if ret:
        objpoints.append(objp)
        
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        print(f"Başarılı: {fname}")
    else:
        print(f"Köşeler bulunamadı, atlanıyor: {fname}")


if len(objpoints) < 10:
    print("HATA: Yeterli veri toplanamadı. Daha fazla fotoğraf çekmelisin!")
    exit()


ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, 
    imgpoints, 
    gray.shape[::-1], 
    None, 
    None
)


np.savez("kamera_matrisi.npz", mtx=mtx, dist=dist)

print("-" * 30)
print(f"RMS Hata Payı (Reprojection Error): {ret:.4f}")

if ret < 1.0:
    print("SONUÇ: KALİBRASYON BAŞARILI (Hassas takip yapılabilir)")
else:
    print("SONUÇ: HATA PAYI YÜKSEK (Işığı düzeltip farklı açılardan tekrar dene)")
print("-" * 30)