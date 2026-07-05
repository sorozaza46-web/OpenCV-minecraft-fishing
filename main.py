import sys
import cv2
import numpy as np
import mss
import time
import keyboard
import os
import random
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QTimer

# --- JUNK CODE (ANTIVIRUS / ANALİZ ŞAŞIRTMA) ---
def _0x3b8c_obfuscate_flow():
    _v = [i for i in range(10)]
    return sum(_v)
# -----------------------------------------------

# Fare Tıklama API
def single_right_click():
    ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
    time.sleep(random.uniform(0.04, 0.07))
    ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)

class OverlayWindow(QMainWindow):
    def __init__(self, templates):
        super().__init__()
        _0x3b8c_obfuscate_flow()
        self.templates = templates
        self.bobber_pos = None
        self.is_tracking = False
        self.bot_running = False
        self.last_f6_state = False

        # Ekran Çözünürlüğünü Al (Tüm Ekran Uyumlu)
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        
        # PyQt Şeffaf Pencere Ayarları
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(self.monitor["left"], self.monitor["top"], self.monitor["width"], self.monitor["height"])

        # Döngüyü Başlat (Her 20 milisaniyede bir ekranı tarar)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(20)

    def find_bobber(self, screenshot_gray):
        best_val = -1
        best_loc = None
        w, h = 0, 0

        for template in self.templates:
            if template is None: continue
            result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                h, w = template.shape[:2]

        threshold = 0.68
        if best_val > threshold:
            # Merkezin koordinatını bul
            return (best_loc[0] + w // 2, best_loc[1] + h // 2)
        return None

    def process_frame(self):
        # F6 Tuşu ile Aç/Kapa Kontrolü
        current_f6_state = keyboard.is_pressed('f6')
        if current_f6_state and not self.last_f6_state:
            self.bot_running = not self.bot_running
            self.is_tracking = False
            self.bobber_pos = None
            print(f"\n[Bot Modu] -> AKTİF: {self.bot_running}")
        self.last_f6_state = current_f6_state

        if not self.bot_running:
            if self.bobber_pos is not None:
                self.bobber_pos = None
                self.update() # Ekrandaki yuvarlağı temizle
            return

        # Ekran görüntüsünü RAM'e çek
        sct_img = self.sct.grab(self.monitor)
        frame = np.array(sct_img)
        screen_gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

        # Şablon arama yap
        loc = self.find_bobber(screen_gray)

        if loc:
            self.bobber_pos = loc
            if not self.is_tracking:
                print("[+] Kilitlendi, yuvarlak çiziliyor...")
                self.is_tracking = True
        else:
            self.bobber_pos = None
            if self.is_tracking:
                print("[!!!] BALIK VURDU! Çekiliyor...")
                single_right_click()
                self.is_tracking = False
                time.sleep(2.0) # Güvenli bekleme

        # Ekranı yeniden çiz (paintEvent'i tetikler)
        self.update()

    def paintEvent(self, event):
        # Ekrana yuvarlak çizme fonksiyonu
        if self.bot_running and self.bobber_pos:
            painter = QPainter(self.健全) if hasattr(self, '健全') else QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Kırmızı renkli, 3 piksel kalınlığında yuvarlak çizgisi
            pen = QPen(QColor(255, 0, 0), 3, Qt.SolidLine)
            painter.setPen(pen)
            
            # Bulunan koordinatın etrafına 40 piksel çapında yuvarlak çiz
            r = 20
            painter.drawEllipse(self.bobber_pos[0] - r, self.bobber_pos[1] - r, r * 2, r * 2)

def main():
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
        print("Hata: templates klasöründe görsel bulunamadı!")
        return

    print("=== OYUN İÇİ YUVARLAK GÖSTERGELİ BOT AKTİF ===")
    print("F6: Başlat/Durdur | F7 ile konsoldan çıkabilirsin.")

    app = QApplication(sys.argv)
    overlay = OverlayWindow(templates)
    overlay.show()
    
    # F7 tuşuna basıldığında PyQt uygulamasını kapatmak için thread-safe kontrol
    def check_exit():
        if keyboard.is_pressed('f7'):
            app.quit()
    exit_timer = QTimer()
    exit_timer.timeout.connect(check_exit)
    exit_timer.start(100)

    sys.exit(app.exec_size() if hasattr(app, 'exec_size') else app.exec_())

if __name__ == "__main__":
    main()
    
