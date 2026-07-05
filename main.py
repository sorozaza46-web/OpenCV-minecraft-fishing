import cv2
import numpy as np
import mss
import time
import keyboard
import os
import random
import ctypes
from colorama import init, Fore

init(autoreset=True)

def find_bobber(templates, screenshot_gray):
    """Tüm ekranda şablonları arar ve en iyi eşleşen konumu (x, y) döndürür."""
    best_val = -1
    best_loc = None
    w, h = 0, 0

    for template in templates:
        if template is None: 
            continue
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            h, w = template.shape[:2]

    # Hassasiyet eşiği. Görseller kaliteliyse 0.65-0.70 arası idealdir.
    threshold = 0.65 
    if best_val > threshold:
        # Mantarın tam merkez koordinatını döndür
        center_x = best_loc[0] + w // 2
        center_y = best_loc[1] + h // 2
        return (center_x, center_y), best_val
    return None, best_val

def right_click():
    """Windows API ile anlık sağ tık gönderir."""
    ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
    time.sleep(random.uniform(0.05, 0.08))
    ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)

def main():
    ctypes.windll.kernel32.SetConsoleTitleW("Advanced Hook Controller v3.0")

    # Şablonları yükle
    templates_dir = 'templates'
    templates = []
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = cv2.imread(os.path.join(templates_dir, filename), 0)
                if img is not None:
                    templates.append(img)
    
    if not templates:
        print(Fore.RED + "Hata: Şablon resimleri bulunamadı!")
        return

    bot_running = False
    last_f6_state = False

    # Durum Yönetimi (State)
    # "START" -> İlk olta atışı
    # "FLYING" -> Oltanın havada süzülme süresi (Tıklamayı engeller)
    # "TRACKING" -> Mantar suya kondu, dikey hareketleri ve partikülleri izliyor
    current_state = "START" 
    
    stable_y = None          # Mantarın sudaki normal Y koordinatı
    bite_counter = 0         # Ani hareket sapma sayacı
    last_seen_time = time.time()

    # Tüm ekranı otomatik kapla (Çözünürlük bağımsız)
    with mss.mss() as sct:
        monitor = sct.monitors[1] # Ana ekranın tamamı

        print(Fore.CYAN + "=== SİSTEM HAZIR (TÜM EKRAN TARANIYOR) ===")
        print("Başlat/Durdur: [F6] | Çıkış: [F7]")

        while True:
            if keyboard.is_pressed('f7'):
                break

            # F6 Aç/Kapa
            current_f6_state = keyboard.is_pressed('f6')
            if current_f6_state and not last_f6_state:
                bot_running = not bot_running
                current_state = "START" # Her açıldığında sıfırdan başla
                print(Fore.GREEN + f"\n[Bot Durumu Değişti] -> AKTİF: {bot_running}")
                time.sleep(0.3)
            last_f6_state = current_f6_state

            if bot_running:
                # Ekran görüntüsünü RAM'e al
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                screen_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # Mantarı tara
                bobber_pos, score = find_bobber(templates, screen_gray)

                # --- DURUM MAKİNESİ (STATE MACHINE) ---
                
                if current_state == "START":
                    print(Fore.YELLOW + "[+] Olta suya fırlatılıyor...")
                    right_click()
                    last_seen_time = time.time()
                    current_state = "FLYING"
                    time.sleep(1.2) # Oltanın havada uçma süresi boyunca ekranı tarama, kör kal.

                elif current_state == "FLYING":
                    if bobber_pos:
                        # Mantar havadan süzülüp suya düştü ve ekranda sabitlendi!
                        stable_y = bobber_pos[1] # Su seviyesindeki ilk Y koordinatını kaydet
                        bite_counter = 0
                        current_state = "TRACKING"
                        print(Fore.BLUE + f"[~] Mantar suya oturdu. Sabit Y Ekseni: {stable_y}")
                    else:
                        # Henüz görünmediyse veya havadaysa aramaya devam et ama sağ tıklama
                        if time.time() - last_seen_time > 4.0: 
                            # 4 saniye geçti ve mantar hiç görünmediyse olta kaçmıştır, resetle
                            current_state = "START"

                elif current_state == "TRACKING":
                    if bobber_pos:
                        current_y = bobber_pos[1]
                        # Sapma hesaplama: Mantar ilk konumuna göre aşağı çekildi mi?
                        # Minecraft'ta aşağı doğru Y ekseni artar (+ piksel)
                        y_diff = current_y - stable_y

                        # Balık partikülleri çıktığında veya su dalgalandığında şablon eşleşme skoru
                        # anlık olarak düşer veya mantar aniden 8-15 piksel aşağı zıplar.
                        if y_diff > 7 or score < 0.52: 
                            bite_counter += 1
                            if bite_counter >= 2: # Yalancı hareketleri önlemek için arka arkaya 2 kare doğrulama
                                print(Fore.GREEN + f"[!!!] BALIK VURDU! (Hassasiyet Değişimi/Aşağı Çekilme saptandı).")
                                right_click() # Balığı çek
                                time.sleep(0.5)
                                current_state = "START" # Yeniden olta atmaya git
                        else:
                            # Her şey yolunda, hafif dalgalanmaları absorbe et ve ana Y seviyesini güncelle
                            bite_counter = max(0, bite_counter - 1)
                            # Yumuşak takip (Mantarın su üstünde yavaşça yüzmesini dengeler)
                            stable_y = int(stable_y * 0.9 + current_y * 0.1)
                        
                        last_seen_time = time.time()
                    else:
                        # Mantar aniden tamamen kaybolduysa (Suya gömülüp partiküller arasında yittiyse)
                        if time.time() - last_seen_time > 0.5: # Yarım saniye boyunca ekranda yoksa çek
                            print(Fore.RED + "[-] Mantar gözden kayboldu! Balık çekiliyor...")
                            right_click()
                            time.sleep(0.5)
                            current_state = "START"

            time.sleep(0.03) # CPU dostu döngü hızı

if __name__ == "__main__":
    main()
    
