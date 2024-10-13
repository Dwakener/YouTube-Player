import requests
import pytube
import cv2
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import random
import os
import time

# Список URL для получения открытых прокси
PROXY_SOURCES = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
    "https://www.proxyscan.io/download?type=http"
]

def get_proxy_list():
    """Получает список прокси с нескольких источников."""
    proxies = []
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                proxies.extend(response.text.splitlines())
        except Exception as e:
            print(f"Не удалось получить прокси с {url}: {e}")
    return proxies

def get_working_proxy(timeout=5):
    """Ищет рабочий прокси с заданным таймаутом."""
    proxies = get_proxy_list()
    random.shuffle(proxies)  # Перемешиваем прокси для случайного выбора

    for proxy in proxies:
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            print(f"Пробую прокси: {proxy}")
            # Тестируем прокси на доступность
            response = requests.get("https://www.youtube.com", proxies=proxy_dict, timeout=timeout)
            if response.status_code == 200:
                print(f"Рабочий прокси найден: {proxy}")
                return proxy_dict
        except Exception as e:
            print(f"Прокси {proxy} не работает: {e}")
    raise Exception("Не удалось найти рабочий прокси.")

class YouTubePlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Player")
        
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=10)
        self.url_entry.insert(0, "Вставьте ссылку на YouTube видео")
        
        #self.url_entry.bind("<Control-v>", self.paste_text)
        #self.url_entry.bind("<Command-v>", self.paste_text)
        
        self.play_button = tk.Button(root, text="Воспроизвести", command=self.start_video_thread)
        self.play_button.pack(pady=10)

        self.cap = None

    def paste_text(self, event):
        try:
            clipboard = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard)
        except tk.TclError:
            messagebox.showerror("Ошибка", "Буфер обмена пуст или недоступен.")

    def start_video_thread(self):
        thread = Thread(target=self.play_video)
        thread.start()

    def play_video(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Введите корректную ссылку.")
            return
        
        try:
            proxy = get_working_proxy()
            yt = pytube.YouTube(url, proxies=proxy)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            video_path = stream.download(filename="video.mp4")

            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                raise Exception("Не удалось открыть видео.")

            while self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    break

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                cv2.imshow("YouTube Player", frame)

                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break

            self.cap.release()
            cv2.destroyAllWindows()
            os.remove(video_path)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка воспроизведения: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubePlayer(root)
    root.mainloop()
