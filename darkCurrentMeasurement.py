import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from scipy import stats
from picamera2 import Picamera2
import time

# === 1. KAMERA AYARLARI ===
picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)

def capture_dark_frames(save_folder, exposure_time_us, num_frames=5):
    """
    Verilen pozlama süresiyle belirli sayıda karanlık görüntü (dark frame) yakala ve kaydet.
    """
    exposure_sec = exposure_time_us / 1_000_000
    folder_name = f"{exposure_sec:.1f}s"
    exposure_folder = os.path.join(save_folder, folder_name)
    os.makedirs(exposure_folder, exist_ok=True)

    picam2.set_controls({
        "AeEnable": False,
        "ExposureTime": exposure_time_us
    })

    picam2.start()
    time.sleep(1)

    print(f"📸 {num_frames} dark frame yakalanıyor @ {exposure_sec:.1f} s...")
    for i in range(num_frames):  # tqdm kaldırıldı
        im = picam2.capture_array()
        img = Image.fromarray(im)
        img.save(os.path.join(exposure_folder, f"frame_{i+1:03d}.tiff"))

    picam2.stop()
    print("✅ Kaydetme tamamlandı.\n")

def loadImage(path):
    im = Image.open(path)
    return np.array(im, np.float32)

def average_dark_frame(folder):
    file_list = sorted([f for f in os.listdir(folder) if f.lower().endswith('.tiff')])
    
    if not file_list:
        print(f"⚠️  Uyarı: '{folder}' klasöründe .tiff dosyası bulunamadı.")
        return None

    acc = None
    for filename in file_list:
        img = loadImage(os.path.join(folder, filename))
        if acc is None:
            acc = np.zeros_like(img)
        acc += img
    avg_img = acc / len(file_list)
    return avg_img

def analyze_dark_current(base_folder, scan_list, exp_times):
    mu_values = []

    print("\n--- Piksel Ortalamaları (Gray Level - ADU) ---")
    for scan, t in zip(scan_list, exp_times):
        folder = os.path.join(base_folder, f"{scan}s")
        if not os.path.exists(folder):
            print(f"❌ Klasör yok: {folder}")
            continue

        avg_image = average_dark_frame(folder)
        if avg_image is None:
            continue

        mu = np.mean(avg_image)
        mu_values.append(mu)
        print(f"- {t:.2f}s pozlama için ortalama ADU: {mu:.2f}")

    if not mu_values:
        print("❌ Yeterli veri yok. Analiz iptal.")
        return

    mu_values = np.array(mu_values)
    exp_times = np.array(exp_times[:len(mu_values)])

    res = stats.linregress(exp_times, mu_values)
    slope = res.slope
    intercept = res.intercept
    r_squared = res.rvalue**2

    print("\n--- Dark Current Analizi ---")
    print(f"Eğim (dark current): {slope:.3f} ADU/s")
    print(f"Y-kesişim (bias): {intercept:.3f} ADU")
    print(f"R²: {r_squared:.4f}")

    plt.figure(dpi=150)
    plt.plot(exp_times, mu_values, 'o-', label='Ortalama ADU')
    plt.plot(exp_times, intercept + slope * exp_times, '--k', label='Doğrusal Uyum')
    plt.xlabel("Pozlama Süresi (s)")
    plt.ylabel("Ortalama Piksel Değeri (ADU)")
    plt.title("Dark Current vs Exposure Time")
    plt.grid(True)
    plt.legend()
    plt.show()

    return mu_values

# === 4. ANA ÇALIŞMA ===
if _name_ == "_main_":
    base_folder = "/home/test/dark_frames"
    exp_time_list_s = [0.1, 0.5, 1, 3, 6]
    exposure_times_us = [int(x * 1_000_000) for x in exp_time_list_s]
    scan_list = [f"{x:.1f}" for x in exp_time_list_s]

    # 1. Dark frame çekimi
    for exp_us in exposure_times_us:
        capture_dark_frames(base_folder, exp_us, num_frames=5)

    # 2. Analiz
    analyze_dark_current(base_folder, scan_list, exp_time_list_s)
