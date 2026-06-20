# Jaw Tracking Backend

Bu proje, webcam goruntusunden ArUco marker tespiti yaparak alt cene hareketini hesaplayan Python/OpenCV backend uygulamasidir. Hesaplanan veri her frame icin JSON formatina cevrilir ve UDP ile Unity tarafina gonderilir.

Unity tarafinda HTTP API, WebSocket veya database gerekmez. Unity sadece UDP portunu dinler ve gelen `jaw_frame` verisini kullanarak STL cene modelini hareket ettirir.

## Genel Akis

```text
Webcam
  |
  v
ArUco Detection
  |
  v
Pose Estimation
  |
  v
Relative Jaw Movement
  |
  v
JawFrame JSON
  |
  v
UDP -> Unity
```

## Klasor Yapisi

```text
Jaw-Tracking/
+-- README.md
+-- requirements.txt
+-- kamera_matrisi.npz
+-- kamera_matrisi.yaml
+-- marker_0.png
+-- marker_1.png
+-- markerlar.pdf
+-- aruco_detect.py
+-- kalibrasyon_hesapla.py
+-- kalibrasyon_yap.py
+-- marker_olustur.py
+-- resim_topla.py
+-- jaw_tracking_backend/
    +-- main.py
    +-- test_sender.py
    +-- camera/
    +-- detection/
    +-- pose/
    +-- motion/
    +-- network/
    +-- models/
    +-- calibration/
    +-- utils/
```

`jaw_tracking_backend/` asil backend kodudur. Kok dizindeki eski dosyalar marker olusturma, kalibrasyon ve eski test akisi icin korunmustur.

## Kurulum

```powershell
pip install -r requirements.txt
```

Gerekli paketler:

- `opencv-contrib-python`
- `numpy`
- `PyYAML`

Not: ArUco modulu icin `opencv-contrib-python` gereklidir.

## Gercek Kamera ile Calistirma

Unity ayni bilgisayarda calisiyorsa:

```powershell
python -m jaw_tracking_backend.main
```

Varsayilan UDP hedefi:

```text
IP: 127.0.0.1
Port: 5055
```

Unity baska bir bilgisayardaysa:

```powershell
python -m jaw_tracking_backend.main --udp-ip 192.168.1.25 --udp-port 5055
```

OpenCV penceresinden cikmak icin `q` tusuna bas.

## Unity Client Test Paketi

Client tarafinda STL dosyasi yuklendikten sonra veri aktarimi ve cene hareketi test edilecekse kamera kullanmaya gerek yoktur. Bunun icin sahte `jaw_frame` verisi gonderen test sender kullanilir.

Unity ayni bilgisayardaysa:

```powershell
python -m jaw_tracking_backend.test_sender
```

Bu komut `127.0.0.1:5055` adresine 30 FPS test verisi gonderir. Veri icinde alt cene belirgin sekilde acilip kapanir gibi sinus hareketi vardir.

Unity baska bilgisayardaysa:

```powershell
python -m jaw_tracking_backend.test_sender --udp-ip 192.168.1.25 --udp-port 5055
```

10 saniyelik test icin:

```powershell
python -m jaw_tracking_backend.test_sender --duration-sec 10
```

Daha da belirgin cene hareketi icin:

```powershell
python -m jaw_tracking_backend.test_sender --amplitude-mm 60 --amplitude-px 220
```

Client tarafinda beklenen sonuc:

- Unity UDP portu `5055` dinliyor olmali.
- STL cene modeli yuklenmis olmali.
- Test sender calisinca model ritmik olarak acilip kapanmali.
- Unity loglarinda `type: jaw_frame` paketleri gorunmeli.

Bu test, kamera ve marker olmadan sadece Unity veri baglantisini ve animasyon tarafini dogrulamak icindir.

## Marker Duzeni

Gercek takipte iki ArUco marker kullanilir:

```text
Marker ID 0 -> Reference Marker
Marker ID 1 -> Jaw Marker
```

Farkli marker ID kullanmak icin:

```powershell
python -m jaw_tracking_backend.main --reference-id 0 --jaw-id 1
```

Marker fiziksel boyutu varsayilan olarak `30 mm` kabul edilir:

```powershell
python -m jaw_tracking_backend.main --marker-size-mm 30
```

## Kalibrasyon

Backend once bu dosyalari okur:

```text
jaw_tracking_backend/calibration/camera_matrix.npy
jaw_tracking_backend/calibration/dist_coeffs.npy
```

Bu dosyalar yoksa kok dizindeki eski kalibrasyon dosyalarina doner:

```text
kamera_matrisi.npz
kamera_matrisi.yaml
```

Kalibrasyon, lens bozulmasini duzeltmek ve marker pose hesabini daha dogru yapmak icin kullanilir.

## Unity'ye Gonderilen JSON

Gercek backend ve test sender ayni ana formati gonderir:

```json
{
  "type": "jaw_frame",
  "frame_id": 123,
  "timestamp_ms": 1750240000,
  "tracking_valid": true,
  "reference_marker": {
    "id": 0,
    "x_px": 340,
    "y_px": 220,
    "angle_deg": 0,
    "confidence": 1.0
  },
  "jaw_marker": {
    "id": 1,
    "x_px": 420,
    "y_px": 350,
    "angle_deg": 12,
    "confidence": 1.0
  },
  "relative": {
    "dx_px": 80,
    "dy_px": 130,
    "dz_px": 10,
    "dtheta_deg": 12,
    "dx_mm": 5.2,
    "dy_mm": 30.1,
    "dz_mm": 2.8
  },
  "pose": {
    "x_mm": 5.2,
    "y_mm": 30.1,
    "z_mm": 500.0,
    "yaw_deg": 3,
    "pitch_deg": 1,
    "roll_deg": 0
  },
  "quality": {
    "latency_ms": 12,
    "fps": 30,
    "confidence": 1.0
  }
}
```

## Dosyalarin Gorevleri

`jaw_tracking_backend/main.py`

Gercek kamera takip uygulamasidir. Kamera, ArUco detection, pose estimation, hareket hesabi ve UDP gonderimini birlestirir.

`jaw_tracking_backend/test_sender.py`

Unity client testi icin kamera gerektirmeyen sahte UDP verisi gonderir.

`jaw_tracking_backend/camera/camera.py`

Kamerayi acar, frame okur ve kalibrasyon varsa undistort uygular.

`jaw_tracking_backend/detection/aruco_detector.py`

ArUco marker merkezini, acisini ve pose icin `rvec/tvec` degerlerini hesaplar.

`jaw_tracking_backend/motion/jaw_motion.py`

Reference marker ile jaw marker arasindaki relatif hareketi hesaplar.

`jaw_tracking_backend/pose/pose_estimator.py`

Jaw marker icin pozisyon ve rotasyon degerlerini uretir.

`jaw_tracking_backend/network/udp_sender.py`

JSON verisini UDP ile Unity tarafina yollar.

`jaw_tracking_backend/models/jaw_frame.py`

Unity'ye giden veri modelini tanimlar.

## Sorun Giderme

### Unity veri almiyor

- Unity portu `5055` dinliyor mu?
- Ayni bilgisayarda test ediliyorsa IP `127.0.0.1` mi?
- Baska bilgisayarda test ediliyorsa dogru IP girildi mi?
- Firewall UDP paketlerini engelliyor mu?
- Unity listener JSON alan adlarini `jaw_frame` formatina gore okuyor mu?

### STL yukleniyor ama cene hareket etmiyor

- Once `test_sender` ile UDP verisinin geldigini dogrula.
- Unity logunda `relative.dy_mm` veya `pose.y_mm` degerleri degisiyor mu bak.
- Model hareketi hangi alana baglandiysa o alanin JSON'da degistigini kontrol et.

### Gercek kamera modunda marker algilanmiyor

- Marker ID'leri dogru mu?
- Markerlar kameraya net gorunuyor mu?
- Isik yeterli mi?
- Marker boyutu `--marker-size-mm` ile dogru girildi mi?

## Kisa Ozet

- Gercek takip icin: `python -m jaw_tracking_backend.main`
- Unity client testi icin: `python -m jaw_tracking_backend.test_sender`
- UDP varsayilani: `127.0.0.1:5055`
- Unity tarafina giden veri tipi: `jaw_frame`
