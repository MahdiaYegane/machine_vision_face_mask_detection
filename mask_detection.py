import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import threading
import time
import numpy as np
import cv2

FONT_PATH = r"E:\OpenCV\Mask Detection\Arad-Medium.ttf"
BOLD_FONT_PATH = r"E:\OpenCV\Mask Detection\Arad-SemiBoldDots3.ttf"
FONT_SIZE_TK = 12
FONT_SIZE_PIL = 18
FONT_COLOR = (255, 255, 0)

pil_font = pil_font_small = pil_font_bold = ImageFont.load_default()

if os.path.exists(FONT_PATH):
    try:
        pil_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PIL)
        pil_font_small = ImageFont.truetype(FONT_PATH, 24)
        pil_font_bold = ImageFont.truetype(BOLD_FONT_PATH, 20) if os.path.exists(BOLD_FONT_PATH) else pil_font
        print("Arad font loaded successfully")
    except Exception as e:
        print(f"error in loading font {e}")
else:
    print(f"font not found {FONT_PATH}")


class EnglishTk:
    @staticmethod
    def _create_text_image(text, font_size=12, bg="#f8f8f8", fg="black", width=None, height=30, bold=False):
        try:
            font = pil_font_bold if bold else ImageFont.truetype(FONT_PATH, font_size + (4 if bold else 0))
        except:
            font = ImageFont.load_default()

        dummy = Image.new("RGB", (1, 1))
        d = ImageDraw.Draw(dummy)
        bbox = d.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        w = width or (text_w + 60)
        h = max(height, text_h + 20)

        def to_rgb(c):
            if isinstance(c, tuple): return c
            c = c.lstrip('#')
            if len(c) == 3: c = ''.join(x*2 for x in c)
            return tuple(int(c[i:i+2], 16) for i in range(0, len(c), 2)) if len(c) in (3,6) else (100,100,100)

        img = Image.new("RGB", (w, h), to_rgb(bg))
        draw = ImageDraw.Draw(img)
        x = (w - text_w) // 2
        y = (h - text_h) // 2
        draw.text((x, y), text, font=font, fill=to_rgb(fg))
        return ImageTk.PhotoImage(img)

    @staticmethod
    def Label(parent, text, **kwargs):
        kwargs.pop('text', None)
        kwargs.pop('font', None)
        kwargs.pop('weight', None)

        bg = kwargs.get('bg', '#f8f8f8')
        fg = kwargs.get('fg', '#333')
        width = kwargs.get('width', None)
        height = kwargs.get('height', 30)
        
        bold = kwargs.pop('weight', '') == 'bold'

        photo = EnglishTk._create_text_image(
            text,
            FONT_SIZE_TK + 2 if bold else FONT_SIZE_TK,
            bg, fg, width, height, bold
        )
        label = tk.Label(parent, image=photo, **kwargs)
        label.image = photo
        return label

    @staticmethod
    def Button(parent, text, **kwargs):
        bg = kwargs.get('bg', '#007bff'); fg = kwargs.get('fg', 'white')
        width = kwargs.get('width', 12) * 12
        height = 40
        photo = EnglishTk._create_text_image(text, FONT_SIZE_TK + 2, bg, fg, width, height, bold=True)
        btn = tk.Button(parent, image=photo, **kwargs)
        btn.image = photo
        return btn

    @staticmethod
    def Entry(parent, **kwargs):
        return tk.Entry(parent, font=(FONT_PATH, FONT_SIZE_TK), justify='left', **kwargs)

    @staticmethod
    def messagebox(title, message):
        win = tk.Toplevel()
        win.title(title); win.geometry("340x180"); win.resizable(False, False); win.configure(bg="#f8f8f8")
        win.transient(); win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - 170
        y = (win.winfo_screenheight() // 2) - 90
        win.geometry(f"340x180+{x}+{y}")
        EnglishTk.Label(win, title, bg="#f8f8f8", fg="#d9534f", height=40, weight='bold').pack(pady=(20, 5))
        EnglishTk.Label(win, message, bg="#f8f8f8", fg="#333", height=40).pack(pady=5)
        tk.Button(win, text="OK", bg="#5cb85c", fg="white", font=(FONT_PATH, FONT_SIZE_TK + 1),
                  command=win.destroy, width=12, height=1).pack(pady=15)




USERNAME = "admin"
PASSWORD = "1234"
CAMERA_INDEX_PHONE = None

def login_window():
    win = tk.Tk()
    
    icon_path = r"E:\OpenCV\Mask Detection\login_icon.png"
    icon = ImageTk.PhotoImage(Image.open(icon_path).resize((30, 30)))

    win.title("ورود"); win.geometry("340x340"); win.resizable(False, False); win.configure(bg="#f8f8f8")
    win.eval('tk::PlaceWindow . center')

    EnglishTk.Label(win, "نام کاربری:", fg="#333", height=35).pack(pady=(40, 5))
    entry_user = EnglishTk.Entry(win); entry_user.pack(pady=5, padx=50, fill=tk.X)

    EnglishTk.Label(win, "رمز عبور:", fg="#333", height=35).pack(pady=(20, 5))
    entry_pass = EnglishTk.Entry(win, show="*"); entry_pass.pack(pady=5, padx=50, fill=tk.X)

    def check():
        if entry_user.get() == USERNAME and entry_pass.get() == PASSWORD:
            win.destroy()
            open_main_app()
        else:
            EnglishTk.messagebox("خطا", "نام کاربری یا رمز اشتباه است!")

    tk.Button(win,image=icon,command=check,bg="#FDF5F5",width=70,height=50,bd=0,highlightthickness=0).pack(pady=25)

    win.icon = icon
    win.mainloop()

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("تشخیص ماسک - ۴ منبع")
        self.root.state('zoomed')
        self.root.configure(bg="black")
        self.running = False
        self.video_file_path = None
        self.threads = []
        self.titles = ["وب (آنلاین)", "گوشی (USB)", "وبکم سیستم", "ویدئو محلی"]
        self.labels = {}

        self.CAM_WIDTH = 700
        self.CAM_HEIGHT = 300
        self.BORDER_THICKNESS = 8

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        total_w = 2 * self.CAM_WIDTH + 3 * 20
        total_h = 2 * self.CAM_HEIGHT + 180 + 4 * 20
        start_x = (screen_w - total_w) // 2
        start_y = (screen_h - total_h) // 2 + 50

        title_label = EnglishTk.Label(
            self.root,
            "سیستم تشخیص ماسک - ۴ منبع همزمان",
            bg="#1a1a1a",
            fg="#ffffff",
            height=70,
            weight='bold'
        )
        title_label.place(x=start_x, y=start_y - 60, width=total_w - 40)

        cam_y = start_y
        positions = [
            (start_x, cam_y),
            (start_x + self.CAM_WIDTH + 20, cam_y),
            (start_x, cam_y + self.CAM_HEIGHT + 20),
            (start_x + self.CAM_WIDTH + 20, cam_y + self.CAM_HEIGHT + 20),
        ]

        for i, title in enumerate(self.titles):
            x, y = positions[i]
            label = tk.Label(root, bg="black", width=self.CAM_WIDTH, height=self.CAM_HEIGHT)
            label.place(x=x, y=y)
            self.labels[title] = label
            self.show_placeholder(label, title)

        control_y = cam_y + 2 * self.CAM_HEIGHT + 40
        control = tk.Frame(root, bg="black")
        control.place(x=start_x, y=control_y, width=total_w - 40)

        button_frame = tk.Frame(control, bg="black")
        button_frame.pack(expand=True)

        EnglishTk.Button(button_frame, "شروع همه", command=self.start_all, bg="#0455ab", fg="#ffffff", height=60).pack(side=tk.LEFT, padx=8)
        EnglishTk.Button(button_frame, "توقف همه", command=self.stop_all, bg="#b91122", fg="#ffffff", height=60).pack(side=tk.LEFT, padx=8)
        EnglishTk.Button(button_frame, "انتخاب ویدئو", command=self.select_video_file, bg="#db6e00",fg="#ffffff", width=180, height=60).pack(side=tk.LEFT, padx=8)
        
        self.mask_detection_active = False
        self.mask_button = EnglishTk.Button(button_frame, "تشخیص ماسک", command=self.toggle_mask_detection, bg="#28a745", fg="#ffffff", height=60)
        self.mask_button.pack(side=tk.LEFT, padx=8)
        
        for title in self.titles:
            self.show_placeholder(self.labels[title], title)

    def draw_text(self, image, text, position, font, color):
        if not text: return image
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=font, fill=color)
        return np.array(img_pil)

    def show_placeholder(self, label, text):
        w, h = self.CAM_WIDTH, self.CAM_HEIGHT
        thickness = self.BORDER_THICKNESS

        img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.rectangle(img, (0, 0), (w, h), (0, 255, 255), thickness)
        inner = img[thickness:-thickness, thickness:-thickness]
        inner[:] = (50, 50, 50)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(img_pil)

        lines = text.split('\n')
        y_offset = thickness + 50
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=pil_font_small)
            text_w = bbox[2] - bbox[0]
            x = (w - text_w) // 2
            draw.text((x, y_offset), line, font=pil_font_small, fill=(200, 200, 200))
            y_offset += 60

        photo = ImageTk.PhotoImage(img_pil)
        label.config(image=photo, text="")
        label.image = photo
        
    def toggle_mask_detection(self):
        self.mask_detection_active = not self.mask_detection_active
        if self.mask_detection_active:
            self.mask_button.configure(bg="#218838")
            messagebox.showinfo("تشخیص ماسک", "تشخیص ماسک فعال شد.")
        else:
            self.mask_button.configure(bg="#28a745")
            messagebox.showinfo("تشخیص ماسک", "تشخیص ماسک غیرفعال شد.")
        
    def select_video_file(self):
        path = filedialog.askopenfilename(
            title="انتخاب فایل ویدئویی",
            filetypes=[("فایل‌های ویدئویی", "*.mp4 *.avi *.mov *.mkv"), ("همه فایل‌ها", "*.*")]
        )
        if path and os.path.exists(path):
            self.video_file_path = path
            EnglishTk.messagebox("موفقیت", f"ویدئو انتخاب شد:\n{os.path.basename(path)}")
            self.show_placeholder(self.labels["ویدئو محلی"], f"ویدئو محلی: {os.path.basename(path)}")

    def start_all(self):
        if self.running: return
        self.running = True

        sources = [
            ("وب (آنلاین)", "https://as9.cdn.asset.aparat.com/aparat-video/dec3e907e222d1a548c18230f676774e27858417-1080p.mp4?wmsAuthSign=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6IjUzNWQzZmQzYjE2ZTJiZmVmMmRlMmNlZDY2YWMyODljIiwiZXhwIjoxNzYzMjI1NDU5LCJpc3MiOiJTYWJhIElkZWEgR1NJRyJ9.wRk2km70hC3muw4e1TRsuzWT7mKD6Kah9dv_sQEvtL0"),
            ("گوشی (USB)", CAMERA_INDEX_PHONE),
            ("وبکم سیستم", 0),
            ("ویدئو محلی", self.video_file_path),
        ]

        for title, src in sources:
            if src is None and title not in ["وب (آنلاین)", "ویدئو محلی"]:
                print(f"[deny] {title}: source is not exist  ")
                continue
            if title == "ویدئو محلی" and not self.video_file_path:
                self.show_placeholder(self.labels[title], "لطفاً یک ویدئو انتخاب کنید.")
                continue
            if title == "گوشی (USB)" and CAMERA_INDEX_PHONE is None:
                self.show_placeholder(self.labels[title], "گوشی از طریق USB متصل نیست")
                continue

            t = threading.Thread(target=self.stream_worker, args=(title, src), daemon=True)
            t.start()
            self.threads.append(t)

    def stop_all(self):
        self.running = False
        for t in self.threads:
            if t.is_alive(): t.join(timeout=0.1)
        self.threads = []
        for title in self.titles:
            self.show_placeholder(self.labels[title], title)

    def stream_worker(self, title, source):
        cap = None
        label = self.labels[title]
        retry_delay = 2.0
        w, h = self.CAM_WIDTH, self.CAM_HEIGHT
        thickness = self.BORDER_THICKNESS

        MAX_DISPLAY_WIDTH = int((w - 2 * thickness) * 0.8)

        while self.running:
            try:
                if not cap or not cap.isOpened():
                    if title == "وبکم سیستم":
                        cap = cv2.VideoCapture(0, cv2.CAP_ANY)
                    elif title == "گوشی (USB)" and isinstance(source, int):
                        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(source)

                    if not cap.isOpened():
                        self.show_placeholder(label, f"{title}\n connecting...")
                        time.sleep(retry_delay)
                        continue

                ret, frame = cap.read()
                if not ret:
                    cap.release(); cap = None
                    time.sleep(retry_delay)
                    continue

                frame_h, frame_w = frame.shape[:2]
                if frame_w > MAX_DISPLAY_WIDTH:
                    scale = MAX_DISPLAY_WIDTH / frame_w
                    new_w = MAX_DISPLAY_WIDTH
                    new_h = int(frame_h * scale)
                else:
                    new_w, new_h = frame_w, frame_h

                resized_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

                final = np.zeros((h, w, 3), dtype=np.uint8)
                cv2.rectangle(final, (0, 0), (w, h), (0, 255, 255), thickness)
                inner = final[thickness:-thickness, thickness:-thickness]
                inner[:] = (50, 50, 50)

                start_x = (w - new_w) // 2
                start_y = (h - new_h) // 2

                y1 = start_y
                y2 = start_y + new_h
                x1 = start_x
                x2 = start_x + new_w

                inner_y1 = max(0, y1 - thickness)
                inner_y2 = min(inner.shape[0], y2 - thickness)
                inner_x1 = max(0, x1 - thickness)
                inner_x2 = min(inner.shape[1], x2 - thickness)

                frame_y1 = max(0, thickness - y1)
                frame_y2 = frame_y1 + (inner_y2 - inner_y1)
                frame_x1 = max(0, thickness - x1)
                frame_x2 = frame_x1 + (inner_x2 - inner_x1)

                if inner_y2 > inner_y1 and inner_x2 > inner_x1:
                    inner[inner_y1:inner_y2, inner_x1:inner_x2] = resized_frame[frame_y1:frame_y2, frame_x1:frame_x2]

                final_rgb = cv2.cvtColor(final, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(final_rgb)
                draw = ImageDraw.Draw(img_pil)
                draw.text((thickness + 10, 5), title, font=pil_font, fill=(255, 255, 255))

                photo = ImageTk.PhotoImage(img_pil)
                label.config(image=photo, text="")
                label.image = photo

            except Exception as e:
                print(f"[ ERROR in {title}]: {e}")
                if cap: cap.release()
                cap = None
                time.sleep(retry_delay)

            time.sleep(0.03)

        if cap and cap.isOpened():
            cap.release()

def open_main_app():
    global CAMERA_INDEX_PHONE

    system_cap = cv2.VideoCapture(0, cv2.CAP_ANY)
    if system_cap.isOpened():
        system_cap.release()

    for i in range(1, 10):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                CAMERA_INDEX_PHONE = i
                cap.release()
                break
            cap.release()
        time.sleep(0.1)

    root = tk.Tk()
    app = VideoApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [app.stop_all(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    login_window()
