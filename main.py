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

    # Eşleşme hassasiyeti
    threshold = 0.68 
    if best_val > threshold:
        return best_loc
    return None

def single_right_click():
    """Yalnızca bir kere sağ tık basar ve bırakır."""
    ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0) # Bas
    time.sleep(random.uniform(0.05, 0.08))
    ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0) # Bırak

def main():
    ctypes.windll.kernel32.SetConsoleTitleW("Strict Hook Engine v5.0")

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
    is_tracking = False 

    print(Fore.CYAN + "=== KONTROLLÜ TEK SEFERLİK BALIK BOTU ===")
    print("Aç/Kapat: [F6] | Çıkış: [F7]")
    print(Fore.YELLOW + "[!] Oltayı siz fırlatın, bot sadece balık vurunca çekecektir.")

    with mss.mss() as sct:
        monitor = sct.monitors[1] # Tüm ekranı tarar

        while True:
            if keyboard.is_pressed('f7'):
                break

            current_f6_state = keyboard.is_pressed('f6')
            if current_f6_state and not last_f6_state:
                bot_running = not bot_running
                is_tracking = False
                print(Fore.GREEN + f"\n[Bot Modu] -> AKTİF: {bot_running}")
                time.sleep(0.2)
            last_f6_state = current_f6_state

            if bot_running:
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                screen_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                bobber_location = find_bobber(templates, screen_gray)

                if bobber_location:
                    if not is_tracking:
                        print(Fore.BLUE + "[+] Mantar ekranda tespit edildi, takibe alındı...")
                        is_tracking = True # Mantar sudaki yerini aldı, tetik kuruldu.
                else:
                    # Ekranda mantar yoksa VE daha önce takibe alındıysa (yani balık vurup aşağı çektiyse/partikül çıktıysa)
                    if is_tracking:
                        print(Fore.GREEN + "[!!!] BALIK VURDU! Oltayı çekiyorum...")
                        single_right_click() # SADECE BİR KERE SAĞ TIKLAR VE DURUR.
                        is_tracking = False  # Tetiği indir, sen yeni olta atana kadar bekleyecek.
                        time.sleep(2.0)      # Yanlışlıkla tekrar tetiklenmesin diye güvenli bekleme süresi
                    else:
                        # Mantar ekranda yoksa ve takipte değilse BOT HİÇBİR ŞEY YAPMAZ, SESSİZCE BEKLER.
                        pass

            time.sleep(0.01) # Minimum gecikme, maksimum tepki hızı

if __name__ == "__main__":
    main()
    
