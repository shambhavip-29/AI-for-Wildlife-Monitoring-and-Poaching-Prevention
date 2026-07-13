import cv2
import threading
import tkinter as tk
from PIL import Image, ImageTk

# Replace this with your mobile stream URL
MOBILE_CAMERA_URL = "http://192.168.1.58:8080/video"


def start_mobile_camera():
    cap = cv2.VideoCapture(MOBILE_CAMERA_URL)
    if not cap.isOpened():
        print("❌ Cannot open mobile camera stream")
        return

    window = tk.Tk()
    window.title("Mobile Camera Stream")
    window.geometry("700x700+20+10")
    window.configure(bg="black")
    window.resizable(False, False)

    video_label = tk.Label(window, bg="black", width=640, height=480)
    video_label.pack(padx=10, pady=10)

    detection_active = True

    def stop_camera():
        nonlocal detection_active
        detection_active = False

    def update_frame():
        nonlocal detection_active
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.config(image=imgtk)

        if detection_active:
            window.after(10, update_frame)
        else:
            cap.release()
            window.destroy()

    # Close button
    tk.Button(window, text="Close Stream", bg="red", fg="white", width=20, command=stop_camera).pack(pady=15)

    # Start frame update
    update_frame()
    window.mainloop()