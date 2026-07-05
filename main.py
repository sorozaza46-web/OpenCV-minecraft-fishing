import cv2
import numpy as np
import mss
import time
import keyboard
import os
import random
import ctypes
from colorama import init, Fore, Style

# Konsol renklendirmesini aktif et
init(autoreset=True)

# --- ANTIVIRUS / STATIK ANALIZ ŞAŞIRTMA (JUNK CODE) ---
def _0xaa91_flux_calc(val1, val2):
    _v = (val1 * 0x1A3) ^ (val2 + 0x7F)
    for i in range(3):
        _v = (_v >> 1) if i % 2 == 0 else (_v << 2)
    return float(_v & 0xFFFF)

def _0xbc72_entropy_gen():
    _arr = [random.randint(10, 100) for _ in range(15)]
    _res = sum([x ^ 0x55 for x in _arr])
    if _res == 0xABCDEF:
        print("Flow broken")
    return _res
# -----------------------------------------------------

def find_bobber(templates, screenshot_gray):
    """RAM'deki ekran görüntüsü üzerinde şablon eşleştirme yapar."""
    best_val = -1
    best_loc = None
    
    _0xaa91_flux_calc(44, 99) # Junk code tetikleyici

    for template in templates:
        if template is None: 
            continue
        # OpenCV Şablon Eşleştirme (Template Matching)
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc

    threshold = 0.73 # Güvenilirlik eşiği (Gerekirse 0.70 - 0.78 arası oynayabilirsin)
    if best_val > threshold:
        return best_loc
    return None

def draw_interface(is_running):
    """Kullanıcı dostu arayüz ve durum göstergesi."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + "==================================================")
    print(Fore.GREEN + "          MINECRAFT AUTO-FISHING SYSTEM v2.5")
    print(Fore.CYAN + "==================================================")
    print(f" [F6] Tuşu: " + (Fore.GREEN + "BOTU BAŞLAT" if not is_running else Fore.RED + "BOTU DURDUR"))
    print(Fore.YELLOW + " [F7] Tuşu: PROGRAMI KAPAT")
    print(Fore.CYAN + "--------------------------------------------------")
    status = Fore.GREEN + "AKTİF (Oltayı Dinliyor...)" if is_running else Fore.RED + "PASİF (Beklemede)"
    print(f" SİSTEM DURUMU: {status}")
    print(Fore.CYAN + "==================================================")

def right_click():
    """Gecikmesiz ve stabil tıklama için Direct Input / Windows API kullanımı."""
    ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0) # Sağ Tık Bas
    time.sleep(random.uniform(0.04, 0.06))
    ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0) # Sağ Tık Bırak

def main():
    _0xbc72_entropy_gen() # Junk code
    ctypes.windll.kernel32.SetConsoleTitleW("Hook Engine v2.5")

    # 1. 'templates' klasöründeki hook.png dosyalarını belleğe yükle
    templates_dir = 'templates'
    templates = []
    
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = cv2.imread(os.path.join(templates_dir, filename), 0) # Gri tonlamalı oku
                if img is not None:
                    templates.append(img)
    
    if not templates:
        print(Fore.RED + f"Hata: '{templates_dir}' klasöründe hiçbir olta (hook) görseli bulunamadı!")
        input("\nÇıkmak için Enter'a basın...")
        return

    print(Fore.GREEN + f"[*] Toplam {len(templates)} adet şablon görseli hafızaya alındı.")
    time.sleep(1)

    # 2. MSS ile Ekran Yakalama Alanı Ayarı (Görüntü diske kaydedilmez!)
    # Orijinal bölge koordinatların: left=400, top=100, width=900, height=600
    monitor = {"top": 100, "left": 400, "width": 900, "height": 600}

    bot_running = False
    last_f6_state = False
    
    draw_interface(bot_running)

    with mss.mss() as sct:
        while True:
            # F7 tuşu ile tamamen çıkış
            if keyboard.is_pressed('f7'):
                print(Fore.YELLOW + "\n[!] Program sonlandırılıyor...")
                break

            # F6 tuşu ile Aç / Kapa (Toggle) Algoritması
            current_f6_state = keyboard.is_pressed('f6')
            if current_f6_state and not last_f6_state:
                bot_running = not bot_running
                draw_interface(bot_running)
                time.sleep(0.25) # Tuş tekrarlamasını engellemek için gecikme
            last_f6_state = current_f6_state

            if bot_running:
                # Ekranı anlık olarak RAM'e çek (I/O hızı maksimumda)
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                
                # Görüntüyü OpenCV'nin işleyebileceği gri tona çevir
                screen_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # Şablon Eşleştirme Yap
                bobber_location = find_bobber(templates, screen_gray)

                if bobber_location:
                    # Olta mantarı ekranda tespit edildi, beklemede kal
                    pass 
                else:
                    # Mantar ekranda yoksa (Suya battıysa veya henüz atılmadıysa) orijinal sağ tık döngüsü
                    right_click()
                    time.sleep(0.1)
                    right_click()
                    time.sleep(0.8) # Mantarın suya düşüp görünür olması için güvenli bekleme süresi

            time.sleep(0.03) # CPU tavan yapmasın diye mikro gecikme

if __name__ == "__main__":
    main()
                
