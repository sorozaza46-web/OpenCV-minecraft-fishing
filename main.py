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

# --- JUNK CODE (ANTIVIRUS / ANALİZ ŞAŞIRTMA) ---
def _0x5f2e_junk_math(a, b):
    _v = (a * 0x2B) ^ (b + 0x1A)
    return float(_v & 0xFF)
# -----------------------------------------------

def find_bobber(templates, screenshot_gray):
    """Ekranda en iyi eşleşen mantarı ve güvenilirlik skorunu bulur."""
    best_val = -1
    best_loc = None

    for template in templates:
        if template is None: 
            continue
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc

    # Hassasiyet eşiği: 0.70 idealdir. Partiküller çıkınca bu skor hızla düşer.
    threshold = 0.70 
    if best_val > threshold:
        return best_loc, best_val
    return None, best_val

def right_click():
    """Windows API ile temiz bir sağ tık kombinasyonu."""
    ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
    time.sleep(random.uniform(0.04, 0.07))
    ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)

def main():
    _0x5f2e_junk_math(10, 20)
    ctypes.windll.kernel32.SetConsoleTitleW("Dynamic Hook Engine v4.0")

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
        print(Fore.RED + "Hata: templates klasöründe görsel bulunamadı!")
        return

    bot_running = False
    last_f6_state = False
    
    # Yeni Mantık Filtresi: Olta şu an takip ediliyor mu?
    is_tracking_bobber = False 

    print(Fore.CYAN + "=== GELİŞMİŞ PARTİKÜL VE HAREKET TAKİP BOTU ===")
    print("Başlat/Durdur: [F6] | Çıkış: [F7]")

    with mss.mss() as sct:
        monitor = sct.monitors[1] # Tüm ekranı tarar

        while True:
            if keyboard.is_pressed('f7'):
                break

            # F6 tuşu ile Aç / Kapa
            current_f6_state = keyboard.is_pressed('f6')
            if current_f6_state and not last_f6_state:
                bot_running = not bot_running
                is_tracking_bobber = False # Durum sıfırlama
                print(Fore.GREEN + f"\n[Bot Modu] -> AKTİF: {bot_running}")
                time.sleep(0.2)
            last_f6_state = current_f6_state

            if bot_running:
                # Görüntüyü RAM'e al
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                screen_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                # Şablon eşleştirmeyi çalıştır
                bobber_location, match_score = find_bobber(templates, screen_gray)

                # --- AKILLI SAĞ TIK MANTIĞI ---
                if bobber_location:
                    # Şablon ekranda net şekilde bulundu! 
                    if not is_tracking_bobber:
                        print(Fore.BLUE + "[+] Olta mantarı başarıyla kilitlendi. Balık bekleniyor...")
                        is_tracking_bobber = True # Artık oltayı takibe aldık, tetik kuruldu.
                    
                    x, y = bobber_location
                    
                else:
                    # Şablon ekranda BULUNAMADI!
                    # Eğer daha önce mantarı kilitlediysek (is_tracking_bobber == True) ve ŞİMDİ bulamıyorsak;
                    # bu durum balığın partiküller çıkararak mantarı aşağı çektiğini (gözden kaybettiğini) gösterir!
                    if is_tracking_bobber:
                        print(Fore.GREEN + "[!!!] BALIK VURDU (Partikül/Aşağı Çekilme Algılandı)! Çekiliyor...")
                        
                        # Orijinal sağ tık kombinasyonun
                        right_click() # Balığı çek
                        time.sleep(0.12)
                        right_click() # Yeni oltayı fırlat
                        
                        is_tracking_bobber = False # Kilidi kaldır, yeni atılan oltanın suya düşmesini bekle
                        time.sleep(1.5) # Oltanın havada süzülüp suya oturması için güvenli süre (Sürekli tıklamayı önler)
                    else:
                        # Eğer bot aktifse ama ekranda hala mantar göremediyse (ilk açılışta veya kaçırma durumunda)
                        # Sistemi tetiklemek için bir kere oltayı fırlatırız.
                        print(Fore.YELLOW + "[*] Ekran taranıyor, olta atılmamış olabilir. İlk atış yapılıyor...")
                        right_click()
                        time.sleep(1.5)

            time.sleep(0.02) # CPU optimizasyonu

if __name__ == "__main__":
    main()
    
