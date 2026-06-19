# Jaw Tracking - Adım Adım Kurulum ve Kullanma Rehberi

Gerçek zamanlı çene hareketi takip sistemi. ArUco marker tespiti ve kamera kalibrasyonu kullanarak, webcam görüntüsünden alt çeneyi izler ve hesaplanan verileri UDP üzerinden Unity uygulamasına gönderir.

**Proje Mimarisi:**
```text
Webcam
  ↓
[1] Resim Toplama & Kalibrasyon (Hazırlık)
  ↓
[2] ArUco Marker Tespiti
  ↓
[3] Pose Tahmini
  ↓
[4] Çene Hareket Hesaplama
  ↓
[5] UDP Veri Gönderimi → Unity
```

---

## Bölüm 1: Hazırlık ve Gerekli Paketler

### 1.1. Gerekli Yazılımlar

- **Python 3.8+**
- **Pip** (Python paket yöneticisi)
- **Webcam** (entegre veya USB)

### 1.2. Paketleri Yükle

Proje kök dizininde terminal açıp şu komutu çalıştırın:

```powershell
pip install -r requirements.txt
```

**Kurulacak paketler:**

| Paket | Amaç |
|-------|------|
| `opencv-contrib-python` | Görüntü işleme ve ArUco modülü (önemli!) |
| `numpy` | Matematiksel işlemler |
| `PyYAML` | YAML dosya okuması (kamera kalibrasyonu) |

> ⚠️ **Önemli:** `opencv-contrib-python` yükleyin, `opencv-python` değil. ArUco modülü sadece `-contrib` versiyonunda bulunur.

---

## Bölüm 2: Marker Oluşturma

ArUco marker, kalibrasyon sırasında ve takip sırasında kamera konumunu belirlemek için kullanılır.

### 2.1. Marker Oluştur

Terminal'de şu komutu çalıştırın:

```powershell
python marker_olustur.py
```

**Çıktı:**
- `marker_0.png` - Referans marker (başa takılır)
- `marker_1.png` - Çene marker'ı (çeneye takılır)
- `markerlar.pdf` - Yazdırılabilir PDF

### 2.2. Marker'ları Hazırla

1. **marker_0.png** ve **marker_1.png** dosyalarını yazdırın
   - Her ikisi de A4 kağıda yazdırılmalı
   - **Fiziksel boyutu önemli!** (Varsayılan: 30mm × 30mm)
   - Cetvel ile ölçüp ayarlayın

2. **Yapıştırma:**
   - `marker_0` → Başa/alına düz şekilde yapıştırın
   - `marker_1` → Çenenin üstüne (düz dişlerin üstüne) yapıştırın

> **Marker boyutu ayarlamak:** marker_olustur.py içinde `marker_size_mm` parametresini değiştirin.

---

## Bölüm 3: Kamera Kalibrasyonu

Kamera hiç kusursuz değildir. Mercek distorsiyonunu (lens distortion) hesaplamak için kalibrasyona ihtiyaç vardır.

### 3.1. Resim Topla

Satranç tahtası (9×6 karelı) kullanarak kalibrasyonlar resimleri toplayın:

```powershell
python resim_topla.py
```

**Kullanım:**
1. Terminal açılırsa, webcam görüntüsü gösterilir
2. **Farklı açılardan ve mesafelerden** satranç tahtasını kameraya gösterin:
   - Yakın (30cm)
   - Uzak (1m+)
   - Sağa, sola, yukarı, aşağı eğim açıları
3. **'s' tuşuna basın** → Her açıda resim kaydedilir
4. **Minimum 20 resim** toplayın (ne kadar çok, o kadar iyi kalibrasyondur)
5. **'q' tuşuna basın** → Bitirip çık

**Çıktı:**
- Resimler `kalibrasyon_resimleri/` klasörüne kaydedilir

### 3.2. Kalibrasyon Hesapla

Toplanan resimleri işleyerek kamera matrisini hesaplayın:

```powershell
python kalibrasyon_hesapla.py
```

**İşlem:**
1. Tüm resimlerdeki satranç tahtası köşelerini tespit eder
2. 3D-2D koordinat eşleştirmesi yapar
3. OpenCV'nin `cv2.calibrateCamera()` fonksiyonuyla hesaplar

**Çıktı:**
- `kamera_matrisi.npz` - NumPy formatında (ikili veri)
- `kamera_matrisi.yaml` - YAML formatında (insan okunabilir)

**kamera_matrisi.yaml örneği:**
```yaml
camera_matrix: !!opencv-matrix
  rows: 3
  cols: 3
  dt: d
  data: [500.0, 0.0, 320.0,
         0.0, 500.0, 240.0,
         0.0, 0.0, 1.0]
dist_coeff: !!opencv-matrix
  rows: 1
  cols: 5
  dt: d
  data: [-0.1, 0.05, 0.0, 0.0, 0.0]
```

> **Kalibrasyonu test etmek:** `kalibrasyon_yap.py` kodunu çalıştırıp pencere açılırsa, kalibrasyonunuz başarılıdır.

---

## Bölüm 4: Görüntü İşleme - ArUco Tespiti

Backend çalıştırılmadan önce marker tespitini test edebilirsiniz.

### 4.1. ArUco Marker'ları Tespit Et

Marker'ları kameraya gösterin ve şu komutu çalıştırın:

```powershell
python aruco_detect.py
```

**Pencere gösterimi:**
- Tespit edilen marker'lar **yeşil dikdörtgenle** çizilir
- Marker ID numarası gösterilir
- Kalman filtresi ile yumuşatılmış hareket gösterilir

**Başarılı tespit:**
- `marker_0` (referans) görülmeli
- `marker_1` (çene) görülmeli

> **Sorun:** Marker'lar görülmüyorsa:
> - Marker boyutu yanlış mı? (30mm olmalı)
> - Aydınlatma yeterli mi?
> - Kamera açısı uygun mu?

---

## Bölüm 5: Backend Sistemi (Real-Time Takip)

Tüm hazırlıklar bittikten sonra, asıl backend uygulamasını çalıştırabilirsiniz.

### 5.1. Backend Mimarisi

```
jaw_tracking_backend/
├── main.py                 ← Ana uygulama (orchestration)
├── camera/
│   └── camera.py          ← Kamera, kalibrasyonu okur, distorsiyon düzeltir
├── detection/
│   └── aruco_detector.py  ← ArUco marker tespiti
├── pose/
│   └── pose_estimator.py  ← Marker konumu (3D pose) hesaplar
├── motion/
│   └── jaw_motion.py      ← Çene hareket vektörü ve açısını hesaplar
├── network/
│   └── udp_sender.py      ← UDP paket gönderimi
├── models/
│   └── jaw_frame.py       ← Veri modeli (JSON formatı)
├── calibration/
│   ├── camera_matrix.npy  ← Kamera matrisi (ikili)
│   └── dist_coeffs.npy    ← Distorsiyon katsayıları (ikili)
└── utils/
    └── fps_counter.py     ← FPS (kare/saniye) hesap
```

### 5.2. Backend'i Başlat

Terminal'de şu komutu çalıştırın:

```powershell
python -m jaw_tracking_backend.main
```

**Ekran çıktısı:**
```
Camera initialized: 640x480
Calibration loaded: kamera_matrisi.npz
Connecting to UDP: 127.0.0.1:5055
Press 'q' to quit...
FPS: 30.0
JawFrame: {"id": 1, "markers": {...}, "motion": {...}}
```

### 5.3. Ayarlar (Komut Satırı Parametreleri)

Backend'i özelleştirmek için parametreler kullanabilirsiniz:

```powershell
# Farklı kamera (örn: webcam 1)
python -m jaw_tracking_backend.main --camera-index 1

# Çözünürlük ayarla (default 640x480)
python -m jaw_tracking_backend.main --width 1280 --height 720

# Marker boyutu (yazdırılan marker'ın gerçek boyutu mm cinsinden)
python -m jaw_tracking_backend.main --marker-size-mm 30.0

# Farklı UDP hedfi (default 127.0.0.1:5055)
python -m jaw_tracking_backend.main --udp-ip 192.168.1.100 --udp-port 5055

# Marker ID'leri (default: ref=0, jaw=1)
python -m jaw_tracking_backend.main --reference-id 0 --jaw-id 1

# OpenCV ön izlemesini kapat (headless mode)
python -m jaw_tracking_backend.main --headless

# Distorsiyon düzeltmesini kapat (test için)
python -m jaw_tracking_backend.main --no-undistort
```

**Tüm ayarlar:**

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|---------|
| `--camera-index` | 0 | Kamera numarası |
| `--width` | 640 | Görüntü genişliği |
| `--height` | 480 | Görüntü yüksekliği |
| `--reference-id` | 0 | Başın (referans) marker ID'si |
| `--jaw-id` | 1 | Çenenin marker ID'si |
| `--marker-size-mm` | 30.0 | Marker fiziksel boyutu (mm) |
| `--calibration-dir` | `jaw_tracking_backend/calibration` | Kalibrasyonu dosya klasörü |
| `--udp-ip` | 127.0.0.1 | UDP hedef IP |
| `--udp-port` | 5055 | UDP hedef port |
| `--headless` | - | Pencere gösterme |
| `--no-undistort` | - | Distorsiyon düzeltmesini kapat |

### 5.4. Veri Akışı (JSON Formatı)

Her frame'de UDP üzerinden gönderilen JSON:

```json
{
  "frame_id": 42,
  "timestamp_sec": 1234567890.123,
  "quality": "good",
  "markers": {
    "reference": {
      "detected": true,
      "id": 0,
      "position_3d": [-5.2, 10.1, 200.5],
      "position_3d_mm": [-5.2, 10.1, 200.5]
    },
    "jaw": {
      "detected": true,
      "id": 1,
      "position_3d": [-8.5, -15.3, 210.2],
      "position_3d_mm": [-8.5, -15.3, 210.2]
    }
  },
  "motion": {
    "delta_x_mm": -3.3,
    "delta_y_mm": -25.4,
    "delta_z_mm": 9.7,
    "total_distance_mm": 27.4,
    "angle_degrees": -82.5,
    "velocity_mm_per_sec": 150.2
  }
}
```

**Alan Açıklamaları:**

| Alan | Tür | Açıklama |
|------|-----|---------|
| `frame_id` | int | Sıralı frame numarası |
| `timestamp_sec` | float | Unix timestamp (saniye.milisaniye) |
| `quality` | str | `good`, `warning`, `error` |
| `markers[*].detected` | bool | Marker tespit edildi mi? |
| `markers[*].position_3d` | [x, y, z] | 3D konum (kamera referansında) |
| `motion.delta_*` | float | Referans marker'a göre çene konumu değişimi |
| `motion.total_distance_mm` | float | Toplam hareket mesafesi |
| `motion.angle_degrees` | float | Hareket yönü açısı (-180 to 180) |

### 5.5. Kod Yapısı Detaylı

#### **camera.py**
- Kamera bağlantısını açar
- `kamera_matrisi.npz` yükler
- Her frame'i distorsiyon düzeltir (undistortion)
- Görüntüyü RGB/grayscale'e çevirir

#### **aruco_detector.py**
- OpenCV ArUco modülü kulllanır
- Marker'ı tespit eder (köşe noktaları)
- Marker ID'sini bulur

#### **pose_estimator.py**
- `cv2.solvePnP()` fonksiyonunu kullanır
- 2D marker köşelerini → 3D konum hesaplar
- Kamera matrisini kullanır (kalibrasyondan)

#### **jaw_motion.py**
- İki marker arasındaki vektörü hesaplar
- Çene açılış/kapanışını mm cinsinden verir
- Hareket yönü açısını hesaplar
- Hız bilgisi ekler

#### **udp_sender.py**
- JSON formatında paketi hazırlar
- UDP socket açar
- Her frame'i belirtilen IP:port'a gönderir
- Hata durumunda loglama yapar

#### **jaw_frame.py**
- Python dataclass'ı
- JSON serialization özellikleri
- Kalite seviyesi enum'ı (good/warning/error)

#### **fps_counter.py**
- Frame rate (FPS) hesaplar
- Ortalama FPS gösterir
- Min/Max FPS yakalar

---

## Bölüm 6: Klasör Yapısı Tam Harita

```
Jaw-Tracking/
│
├── README.md                          ← Bu dosya
├── requirements.txt                   ← Python paketleri
│
├── [1] MARKER OLUŞTURMA
├── marker_olustur.py                  ← Marker PNG oluştur
├── marker_0.png                       ← Başa yapıştırılacak marker
├── marker_1.png                       ← Çeneye yapıştırılacak marker
├── markerlar.pdf                      ← Yazdırılabilir PDF
│
├── [2] KALİBRASYON
├── resim_topla.py                     ← Kalibrasyon resimleri topla
├── kalibrasyon_hesapla.py             ← Kamera matrisi hesapla
├── kalibrasyon_yap.py                 ← Kalibrasyonu test et
├── kamera_matrisi.npz                 ← İkili kalibrasyonu dosyası ⭐
├── kamera_matrisi.yaml                ← Okunabilir kalibrasyonu dosyası
├── kalibrasyon_resimleri/             ← Toplanan resimler
│   ├── img_0.jpg
│   ├── img_1.jpg
│   └── ...
│
├── [3] GÖRÜNTÜ İŞLEME TEST
├── aruco_detect.py                    ← Marker tespiti test
│
└── [4] BACKEND (ASIL SISTEM)
    └── jaw_tracking_backend/
        ├── __init__.py
        ├── main.py                    ← ⭐ Burayı çalıştırın!
        │
        ├── camera/
        │   ├── __init__.py
        │   └── camera.py              ← Kamera sınıfı
        │
        ├── detection/
        │   ├── __init__.py
        │   └── aruco_detector.py      ← Marker tespiti sınıfı
        │
        ├── pose/
        │   ├── __init__.py
        │   └── pose_estimator.py      ← Pose hesaplama sınıfı
        │
        ├── motion/
        │   ├── __init__.py
        │   └── jaw_motion.py          ← Çene hareketi sınıfı
        │
        ├── network/
        │   ├── __init__.py
        │   └── udp_sender.py          ← UDP gönderimi sınıfı
        │
        ├── models/
        │   ├── __init__.py
        │   └── jaw_frame.py           ← JSON veri modeli
        │
        ├── calibration/
        │   ├── camera_matrix.npy      ← Kamera matrisi
        │   └── dist_coeffs.npy        ← Distorsiyon katsayıları
        │
        └── utils/
            ├── __init__.py
            └── fps_counter.py          ← FPS hesapla
```

---

## Bölüm 7: Hızlı Başlama Kontrol Listesi

Sırasıyla yapılması gereken işlemler:

- [ ] **Paketler yüklü mü?** → `pip install -r requirements.txt`
- [ ] **Marker oluşturuldu mu?** → `python marker_olustur.py`
- [ ] **Marker'lar yapıştırıldı mı?** → Başa ve çeneye yapıştırın
- [ ] **Kalibrasyonu resimler toplandı mı?** → `python resim_topla.py` (20+ resim)
- [ ] **Kalibrasyonu hesaplandı mı?** → `python kalibrasyon_hesapla.py`
- [ ] **`kamera_matrisi.npz` var mı?** → Kontrol edin
- [ ] **Marker tespiti çalışıyor mu?** → `python aruco_detect.py` ile test edin
- [ ] **Backend başlatılabilir mi?** → `python -m jaw_tracking_backend.main`
- [ ] **UDP paketleri gönderiliyor mu?** → Unity tarafında kontrol edin

---

## Bölüm 8: Sorun Giderme

### **Marker'lar görülmüyor**
1. Marker boyutu doğru yazılı mı? (30mm)
2. Marker yüksek kontrast mı? (siyah/beyaz)
3. Aydınlatma yeterli mi?
4. Kamera temiz mi?

### **Kalibrasyonu başarısız**
1. 20+ resim toplandı mı?
2. Satranç tahtası tüm açılardan görülüyor mu?
3. Resimler netli mi?

### **Backend hatasız başlıyor ama UDP gelmiyorum**
1. Firewall UDP'yi engellemiyor mu?
2. UDP IP ve port doğru mu?
3. Marker'lar tespit ediliyor mu?

### **Düşük FPS (< 20 fps)**
1. Çözünürlüğü azaltın: `--width 480 --height 360`
2. Kamera indeksini kontrol edin: `--camera-index`
3. Sistemi yeniden başlatın

---

## Bölüm 9: İleri Kullanım

### **Uzak Bilgisayardaki Unity'e Bağlan**

Unity başka bir bilgisayardaysa:

```powershell
python -m jaw_tracking_backend.main --udp-ip 192.168.1.50 --udp-port 5055
```

(192.168.1.50 yerine Unity bilgisayarının IP'sini yazın)

### **Kalibrasyonu Başka Bir Bilgisayardan Transferi**

Başka bir bilgisayarda kalibrasyonu yapmak isterseniz:

1. Kalibrasyonu yapılan bilgisayardan `kamera_matrisi.npz` dosyasını kopyalayın
2. Hedef bilgisayarın proje kök dizinine yapıştırın
3. Backend başlatırken şunu yazın:
   ```powershell
   python -m jaw_tracking_backend.main --fallback-calibration-base kamera_matrisi
   ```

---

## Bölüm 10: Teknik Detaylar

### **Kamera Kalibrasyonu Nedir?**

Gerçek kameralar kusurludur:
- **Lens distorsiyonu:** Görüntü eğri görülür
- **Asimetrik kamera matrisi:** Piksel birimleri eşit değil

Kalibrasyonu:
1. Bilinen geometri (satranç tahtası) kullanır
2. 2D görüntü piksellerini → 3D gerçek dünya koordinatlerine eşleştir
3. Distorsiyon katsayılarını hesaplar
4. Kamera matrisi çıkarır

**Formül:**
```
p_2d = K * [R | t] * P_3d
```

Burada:
- `K` = Kamera matrisi (intrinsic)
- `R` = Rotasyon matrisi
- `t` = Translasyon vektörü (konum)
- `P_3d` = 3D dünya koordinatı
- `p_2d` = 2D görüntü koordinatı

### **ArUco Marker Tespiti Nasıl Çalışır?**

1. Görüntüyü Gri-ölçeğe çevirir
2. İkili hale dönüştürür (siyah/beyaz)
3. Konturs bulur
4. Dikdörtgen kontur'ları ArUco marker'ı olarak test eder
5. İç bitmap patternini karşılaştırır
6. Marker ID'sini bulur

### **PnP (Perspective-n-Point) Çözümü**

2D marker köşeleri → 3D konum hesaplamak için `cv2.solvePnP()` kullanılır:

```
Input:  2D marker köşeleri (pixellerden)
        Kamera matrisi (kalibrasyondan)
Output: Marker'ın 3D konum (x, y, z)
        Marker'ın rotasyonu (euler açıları)
```

---

## Bölüm 11: Performans Notları

- **Hedef FPS:** 30 FPS
- **Tipik gecikme:** 50-100ms (kalibrasyona göre değişir)
- **UDP paket boyutu:** ~500 bytes
- **CPU kullanımı:** ~15-25% (modern CPU'da)

---

## Bölüm 12: Lisans ve Kaynaklar

- **OpenCV:** Apache 2.0 License
- **NumPy:** BSD License
- **PyYAML:** MIT License

Yapıldığı açık kaynak kütüphaneler:
- OpenCV ArUco (Kalibrasyon + Marker Tespiti)
- NumPy (Matematiksel işlemler)
- Kalman Filtresi (hareket yumuşatması)
python -m jaw_tracking_backend.main --udp-ip 192.168.1.25 --udp-port 5055
```

OpenCV önizleme penceresinden çıkmak için `q` tuşuna bas.

## Marker Düzeni

Sistem iki ArUco marker kullanır:

```text
Marker ID 0 -> Reference Marker
Marker ID 1 -> Jaw Marker
```

Reference Marker üst çene veya kafa referansıdır. Jaw Marker alt çeneye yerleştirilir ve hareketi takip edilir.

Farklı marker ID kullanmak için:

```powershell
python -m jaw_tracking_backend.main --reference-id 0 --jaw-id 1
```

Marker fiziksel boyutu varsayılan olarak `30 mm` kabul edilir:

```powershell
python -m jaw_tracking_backend.main --marker-size-mm 30
```

## Kalibrasyon

Backend önce şu dosyaları okur:

```text
jaw_tracking_backend/calibration/camera_matrix.npy
jaw_tracking_backend/calibration/dist_coeffs.npy
```

Bu dosyalar yoksa kök dizindeki eski kalibrasyon dosyalarına döner:

```text
kamera_matrisi.npz
kamera_matrisi.yaml
```

Kalibrasyon, lens bozulmasını düzeltmek ve marker pose hesabını daha doğru yapmak için kullanılır.

## Sistem Nasıl Çalışır?

1. `main.py` kamerayı açar.
2. Her frame OpenCV ile okunur.
3. `ArucoDetector` görüntüdeki markerları bulur.
4. Marker `0` ve marker `1` aynı anda görünüyorsa takip geçerli olur.
5. Reference marker ile jaw marker arasındaki relatif hareket hesaplanır.
6. Jaw marker için 3D pozisyon ve rotasyon değerleri çıkarılır.
7. Veriler `JawFrame` modeline yerleştirilir.
8. JSON verisi UDP ile Unity tarafına gönderilir.

Marker'lardan biri görünmüyorsa `tracking_valid` değeri `false` gönderilir.

## Unity'ye Gönderilen JSON

Her frame için örnek veri:

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
    "angle_deg": 5,
    "confidence": 1.0
  },
  "jaw_marker": {
    "id": 1,
    "x_px": 420,
    "y_px": 350,
    "angle_deg": 18,
    "confidence": 1.0
  },
  "relative": {
    "dx_px": 80,
    "dy_px": 130,
    "dz_px": 10,
    "dtheta_deg": 13,
    "dx_mm": 5.2,
    "dy_mm": 30.1,
    "dz_mm": 2.8
  },
  "pose": {
    "x_mm": 5.2,
    "y_mm": 30.1,
    "z_mm": 2.8,
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

## Backend Dosyaları

`jaw_tracking_backend/main.py`

Uygulamanın ana giriş noktasıdır. Kamera, marker detection, hareket hesabı, pose estimation ve UDP gönderimini birleştirir.

`jaw_tracking_backend/camera/camera.py`

Webcam'i açar, frame okur ve varsa kamera kalibrasyonunu uygular.

`jaw_tracking_backend/detection/aruco_detector.py`

ArUco markerları bulur. Marker merkezi, açısı ve pose için gerekli `rvec/tvec` değerlerini üretir.

`jaw_tracking_backend/motion/jaw_motion.py`

Reference marker ile jaw marker arasındaki hareket farkını hesaplar:

- `dx_px`
- `dy_px`
- `dz_px`
- `dtheta_deg`
- `dx_mm`
- `dy_mm`
- `dz_mm`

`jaw_tracking_backend/pose/pose_estimator.py`

Jaw marker için pozisyon ve rotasyon hesaplar:

- `x_mm`
- `y_mm`
- `z_mm`
- `yaw_deg`
- `pitch_deg`
- `roll_deg`

`jaw_tracking_backend/network/udp_sender.py`

JSON verisini UDP ile Unity'ye gönderir.

`jaw_tracking_backend/models/jaw_frame.py`

Unity'ye gönderilecek veri modelini tanımlar.

`jaw_tracking_backend/utils/fps_counter.py`

Anlık FPS değerini hesaplar.

## Faydalı Komutlar

Farklı kamera index'i ile çalıştır:

```powershell
python -m jaw_tracking_backend.main --camera-index 1
```

Çözünürlüğü değiştir:

```powershell
python -m jaw_tracking_backend.main --width 1280 --height 720
```

Önizleme penceresi açmadan çalıştır:

```powershell
python -m jaw_tracking_backend.main --headless
```

Kamera undistort işlemini kapat:

```powershell
python -m jaw_tracking_backend.main --no-undistort
```

## Sorun Giderme

### `cv2.aruco` bulunamıyor

Yanlış OpenCV paketi kurulmuş olabilir:

```powershell
pip install opencv-contrib-python
```

### Kamera açılmıyor

Farklı kamera index'i dene:

```powershell
python -m jaw_tracking_backend.main --camera-index 1
```

### Unity veri almıyor

Kontrol listesi:

- Unity tarafı UDP portu `5055` dinliyor mu?
- Python tarafındaki `--udp-ip` doğru mu?
- Aynı bilgisayarda test ediliyorsa IP `127.0.0.1` olmalı.
- Farklı bilgisayarlarda test ediliyorsa iki cihaz aynı ağda olmalı.
- Firewall UDP paketlerini engellememeli.

### Marker algılanmıyor

Kontrol listesi:

- Marker ID'leri doğru mu?
- Markerlar kameraya net görünüyor mu?
- Işık yeterli mi?
- Marker fiziksel boyutu `--marker-size-mm` ile doğru girildi mi?

## Kısa Özet

`Jaw Tracking Backend`, kamera görüntüsünden alt çene hareketini gerçek zamanlı hesaplar ve Unity'ye UDP üzerinden JSON veri gönderir. Unity sadece bu veriyi dinler ve görselleştirir.
