import cv2
import cv2.aruco as aruco
import numpy as np


aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)


marker_size_mm = 30  
dpi = 600           

size_px = int((marker_size_mm / 25.4) * dpi)


marker0 = aruco.generateImageMarker(aruco_dict, 0, size_px, borderBits=1)
marker1 = aruco.generateImageMarker(aruco_dict, 1, size_px, borderBits=1)

cv2.imwrite("UST_CENE_sabit_ID0.png", marker0)
cv2.imwrite("ALT_CENE_hareketli_ID1.png", marker1)

print("--- Klinik Üretim Raporu ---")
print(f"Hedef Boyut: {marker_size_mm} mm")
print(f"Çözünürlük: {size_px}x{size_px} piksel")
print(f"Baskı Kalitesi: {dpi} DPI")
print("Önemli: Yazdırırken 'Gerçek Boyut' (100% scale) seçeneğini kullanın!")