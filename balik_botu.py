"""
Minecraft Otomatik Balık Botu (Görüntü Tabanlı)
=================================================
Ekranın orta bölgesinden bir kare alan alır, bu alandaki piksel değişimini
(şamandıranın sıçraması, kabarcık/partikül efekti) izler. Değişim eşiği
aşıldığında otomatik olarak sağ tık yapar (balığı çeker), sonra tekrar
sağ tık yapıp oltayı yeniden atar.

KURULUM:
    pip install mss numpy pyautogui keyboard

ÖNEMLİ NOTLAR:
- Botu başlatmadan önce Minecraft'ta olta elinde olmalı ve karakterin
  suya bakıyor olması gerekir (bölge, ekranın tam ortasını, yani nişan
  noktasının olduğu yeri hedefler).
- 'keyboard' kütüphanesi Windows'ta genelde YÖNETİCİ olarak çalıştırma
  ister, yoksa F6/F8 kısayolları algılanmayabilir.
- Fare imlecini ekranın sol üst köşesine götürürsen (pyautogui failsafe)
  script otomatik durur - acil durdurma için kullanabilirsin.
- Birçok sunucu otomasyon/macro kullanımını yasaklar, kurallara dikkat et.
  Bu araç yalnızca kendi hesabınla, izin verilen ortamlarda kullanım
  içindir.

KULLANIM:
    python balik_botu.py
    F8  -> menüyü göster/gizle
    F6  -> botu başlat/durdur (menüdeki butonla da yapılabilir)
"""

import time
import threading
import tkinter as tk
from tkinter import ttk

import numpy as np
import mss
import pyautogui
import keyboard

pyautogui.FAILSAFE = True   # fare sol üst köşeye gidince script durur (acil fren)
pyautogui.PAUSE = 0


class FishingBot:
    def __init__(self):
        self.running = False
        self.region_size = 140     # izlenen karenin kenar uzunluğu (px)
        self.sensitivity = 18.0    # ne kadar düşükse o kadar hassas tetiklenir
        self.cast_delay = 0.6      # atıştan sonra "sakinleşme" süresi (saniye)
        self.check_interval = 0.05 # saniyede ~20 kontrol
        self.status = "Durduruldu"
        self.thread = None
        self.sct = mss.mss()

    def get_region(self):
        """Ekranın tam ortasında, ayarlanan boyutta bir kare bölge döndürür."""
        screen = self.sct.monitors[1]
        cx = screen["left"] + screen["width"] // 2
        cy = screen["top"] + screen["height"] // 2
        half = self.region_size // 2
        return {
            "left": cx - half,
            "top": cy - half,
            "width": self.region_size,
            "height": self.region_size,
        }

    def grab(self, region):
        img = np.array(self.sct.grab(region))
        return img[:, :, :3].astype(np.int16)  # BGRA -> BGR, taşma olmasın diye int16

    def cast(self):
        """Oltayı atmak/çekmek için sağ tık (başlangıçta da bu kullanılır)."""
        self.status = "Olta atılıyor..."
        pyautogui.click(button="right")
        time.sleep(self.cast_delay)

    def reel(self):
        self.status = "Baloncuk/partikül algılandı, çekiliyor!"
        pyautogui.click(button="right")
        time.sleep(0.4)

    def loop(self):
        region = self.get_region()
        self.cast()  # girişte de sağ tık ile ilk atışı yapar
        baseline = self.grab(region)
        last_cast_time = time.time()

        while self.running:
            time.sleep(self.check_interval)
            region = self.get_region()  # boyut menüden değiştirilmiş olabilir
            frame = self.grab(region)

            diff = np.abs(frame - baseline)
            score = float(diff.mean())

            # atıştan hemen sonraki su hareketini yanlış algılamayı azaltmak için bekle
            if time.time() - last_cast_time > self.cast_delay + 0.3:
                if score > self.sensitivity:
                    self.reel()
                    time.sleep(0.3)
                    self.cast()
                    baseline = self.grab(region)
                    last_cast_time = time.time()
                    continue

            # baseline'ı yavaşça güncelle (ışık/gölge gibi doğal değişimlere uyum sağlasın)
            baseline = baseline * 0.9 + frame * 0.1
            self.status = f"İzleniyor... (skor: {score:.1f} / eşik: {self.sensitivity:.0f})"

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        self.status = "Durduruldu"


class BotMenu:
    def __init__(self, bot: FishingBot):
        self.bot = bot
        self.visible = True

        self.root = tk.Tk()
        self.root.title("Balık Botu")
        self.root.geometry("300x300")
        self.root.attributes("-topmost", True)

        ttk.Label(self.root, text="Minecraft Balık Botu", font=("Segoe UI", 12, "bold")).pack(pady=8)

        self.status_var = tk.StringVar(value=self.bot.status)
        ttk.Label(self.root, textvariable=self.status_var, wraplength=260).pack(pady=4)

        self.start_btn = ttk.Button(self.root, text="Başlat (F6)", command=self.toggle_bot)
        self.start_btn.pack(pady=8)

        ttk.Label(self.root, text="Hassasiyet (düşük = daha hassas)").pack()
        self.sens_slider = ttk.Scale(self.root, from_=5, to=60, orient="horizontal",
                                      command=self.update_sens)
        self.sens_slider.set(self.bot.sensitivity)
        self.sens_slider.pack(fill="x", padx=20)

        ttk.Label(self.root, text="Bölge Boyutu (px)").pack()
        self.size_slider = ttk.Scale(self.root, from_=60, to=320, orient="horizontal",
                                      command=self.update_size)
        self.size_slider.set(self.bot.region_size)
        self.size_slider.pack(fill="x", padx=20)

        ttk.Label(
            self.root,
            text="F8: Menüyü göster/gizle\nF6: Botu başlat/durdur\nFareyi sol üst köşeye götür: acil durdurma",
            font=("Segoe UI", 8), justify="center"
        ).pack(pady=12)

        keyboard.add_hotkey("f6", self.toggle_bot)
        keyboard.add_hotkey("f8", self.toggle_menu)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh()

    def toggle_bot(self):
        if self.bot.running:
            self.bot.stop()
            self.start_btn.config(text="Başlat (F6)")
        else:
            self.bot.start()
            self.start_btn.config(text="Durdur (F6)")

    def toggle_menu(self):
        if self.visible:
            self.root.withdraw()
        else:
            self.root.deiconify()
        self.visible = not self.visible

    def update_sens(self, val):
        self.bot.sensitivity = float(val)

    def update_size(self, val):
        self.bot.region_size = int(float(val))

    def refresh(self):
        self.status_var.set(self.bot.status)
        self.root.after(150, self.refresh)

    def on_close(self):
        self.bot.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    bot = FishingBot()
    menu = BotMenu(bot)
    menu.run()
