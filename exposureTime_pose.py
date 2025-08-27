import subprocess
import os

# Kullanılacak pozlama süreleri (saniye cinsinden)
exposure_times = [0.01, 0.05, 0.1, 0.2, 0.3]
frame_count = 100

# Çıktı klasörü
output_dir = "/home/test/Desktop/test_frames"
os.makedirs(output_dir, exist_ok=True)

for exp in exposure_times:
    exp_us = int(exp * 1_000_000)  # Pozlama süresini mikro saniyeye çevir
    exp_dir = os.path.join(output_dir, f"{exp}s")
    os.makedirs(exp_dir, exist_ok=True)

    print(f"\n--- {exp}s pozlama ile çekim başlıyor ---")
    for i in range(frame_count):
        filename = os.path.join(exp_dir, f"frame_{i+1:03d}.jpg")
        cmd = [
            "libcamera-still",
            "-n",                       # Önizleme kapalı
            "--shutter", str(exp_us),  # Pozlama süresi
            "-o", filename,            # Çıktı dosyası
            "-t", "100"                # Bekleme süresi (ms)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{filename} kaydedildi.")

print("\n✅ Tüm çekimler tamamlandı.")