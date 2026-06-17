import cv2
import numpy as np
import glob
import yaml

# Klasördeki resimlerle uyuşması için iç köşe sayıları (8, 5)
CHECKERBOARD = (9, 6) 

# Satranç tahtasındaki tek bir karenin gerçek fiziksel boyutu (Milimetre cinsinden)
# Cetvelle ölçüp buraya tam değerini yazın. Örn: 25.0 mm
SQUARE_SIZE = 24.0  

# Dünyadaki 3D koordinat haritasını hazırlama (Z=0 düzlemi)
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

objpoints = [] # Gerçek dünyadaki 3B noktalar havuzu
imgpoints = [] # Resimdeki 2B piksel noktaları havuzu

# Kaydedilen resimleri listele
images = glob.glob('kalibrasyon_resimleri/img_*.jpg')

if len(images) == 0:
    print("Hata: 'kalibrasyon_resimleri' klasöründe 'img_' ile başlayan resim bulunamadı!")
    print("Önce resim_topla.py kodunu çalıştırıp 's' tuşu ile resim kaydetmelisiniz.")
    exit()

print(f"{len(images)} adet resim doğrulanıyor ve işleniyor...")

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Köşeleri resim üzerinde tekrar bul
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        objpoints.append(objp)
        
        # Matematiksel hassasiyeti alt-piksel (sub-pixel) seviyesine çıkarma
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

# Çözünürlük boyutunu al
h, w = gray.shape[:2]

print("Matematiksel kamera kalibrasyon matrisi hesaplanıyor, lütfen bekleyin...")
# OpenCV iç parametre hesaplama fonksiyonu
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, (w, h), None, None)

print("\n--- KALİBRASYON TAMAMLANDI ---")
print(f"RMS Yeniden İzdüşüm Hatası (Re-projection Error): {ret}")
print("Bu değerin 0.5'in altında olması sistemin milimetrik doğruluğu için çok iyidir.")

# Verileri çene takip kodunun (Samet ve Diyar'ın yazacağı altyapının) okuyabileceği şekilde kaydetme
calibration_data = {
    "camera_matrix": mtx.tolist(),
    "dist_coeff": dist.tolist(),
    "rms_error": float(ret)
}

# Çıktıyı kalıcı bir dosyaya yazıyoruz
with open("kamera_matrisi.yaml", "w") as f:
    yaml.dump(calibration_data, f)

print("Başarılı! 'kamera_matrisi.yaml' dosyası klasörünüzde oluşturuldu. İşlem bitti.")