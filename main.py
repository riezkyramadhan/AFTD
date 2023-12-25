
import cv2
import os
import sys
import signal
import time
import numpy as np
import math
from scipy.interpolate import griddata
from edge_impulse_linux.image import ImageImpulseRunner
from sound import *
import tkinter as tk
import cv2
from amg import *
from PIL import Image, ImageTk
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

runner = None
show_camera = True
if (sys.platform == 'linux' and not os.environ.get('DISPLAY')):
    show_camera = False
def rounded(angka):
    value= math.floor(angka * 100) / 100.0
    return value
def now():
    return round(time.time() * 1000)
def exit_fullscreen(event):
    root.attributes('-fullscreen', False)


def get_webcams():
    port_ids = []
    for port in range(5):
        print("Looking for a camera in port %s:" %port)
        camera = cv2.VideoCapture(port)
        if camera.isOpened():
            ret = camera.read()[0]
            if ret:
                backendName =camera.getBackendName()
                w = camera.get(3)
                h = camera.get(4)
                print("Camera %s (%s x %s) found in port %s " %(backendName,h,w, port))
                port_ids.append(port)
            camera.release()
    return port_ids


def rounded(angka):
    x = math.floor(angka * 100) / 100.0
    return x

def help():
    print('python classify.py <path_to_model.eim> <Camera port ID, only required when more than 1 camera is present>')

heatmap_image = None

def update_heatmap_label(label):
    global heatmap_image
    while True:
        if heatmap_image is not None:
            label.configure(image=heatmap_image)
            label.image = heatmap_image
        time.sleep(0.1)
def main_right(heatmap_label,cam_label,videoCaptureDeviceId):
    flatR_counter = 0
    flatR_threshold =4
    tempR_counter = 0
    tempR_threshold = 4

    model = "modelfile.eim"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)
    print('MODEL: ' + modelfile)

    with ImageImpulseRunner(modelfile) as runner:
        try:
            model_info = runner.init()
            print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
            labels = model_info['model_parameters']['labels']
            camera = cv2.VideoCapture(videoCaptureDeviceId)
            ret = camera.read()[0]
            if ret:
                backendName = camera.getBackendName()
                w = camera.get(3)
                h = camera.get(4)
                print("Camera %s (%s x %s) in port %s selected." %(backendName,h,w, videoCaptureDeviceId))
                camera.release()
            else:
                raise Exception("Couldn't initialize selected camera.")

            next_frame = 10 

            for res, img in runner.classifier(videoCaptureDeviceId):
                if (next_frame > now()):
                    time.sleep((next_frame - now()) / 1000)
                if "classification" in res["result"].keys():
                    FULL = res['result']['classification']['full']
                    FLAT = res['result']['classification']['flat']
                    NO_TIRE = res['result']['classification']['no_tire']
                    pixels = sensorR.readPixels()
                    pixels = [map(p, 27, 39, 0, COLORDEPTH - 1) for p in pixels]
                    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
                    image = np.zeros((height, width, 3), dtype=np.uint8)
                    for ix, row in enumerate(bicubic):
                        for jx, pixel in enumerate(row):
                            color = colors[constrain(int(pixel), 0, COLORDEPTH - 1)]
                            image[int(displayPixelHeight * ix):int(displayPixelHeight * (ix + 1)),
                                int(displayPixelWidth * jx):int(displayPixelWidth * (jx + 1))] = color
                    
                    avgR_temp = np.mean(sensorR.readPixels())
                    valueR_temp = int(rounded(avgR_temp))
                    TEMPERATURE2_button.config(text=f'{avgR_temp:.2f}°C')
                    if valueR_temp > 50 :
                        tempR_counter += 1
                        if tempR_counter >= tempR_threshold:
                            Alarm_SB.config(text="NORMAL")
                            Alarm_button.configure(bg="red")
                            Alarm_SB.configure(bg="red")
                            Alarm_SB.config(text="WARNING")
                            play_audio(suhu_file)
                            time.sleep(1)
                            Alarm_SB.config(text="NORMAL")
                            Alarm_SB.configure(bg="white")
                            Alarm_button.configure(bg="white")
                            tempR_counter = 0
                    if FULL > 0.7:
                        CLASS_LEFT_button.config(text='FULL')
                        COEF_LEFT_button.config(text= str(rounded(FULL))+'%')
                    elif FLAT > 0.8:
                        CLASS_LEFT_button.config(text='FLAT')
                        COEF_LEFT_button.config(text= str(rounded(FLAT))+'%')
                        flatR_counter += 1
                        if flatR_counter >= flatR_threshold:
                            Alarm_button.configure(bg="red")
                            Alarm_TB.configure(bg="red")
                            Alarm_TB.config(text="WARNING")
                            play_audio(kempis_file)
                            time.sleep(1)
                            Alarm_TB.config(text="NORMAL")
                            Alarm_button.configure(bg="white")
                            Alarm_TB.configure(bg="white")
                            flatR_counter=0
                    elif NO_TIRE > 0.9:
                        CLASS_LEFT_button.config(text='NO TIRE')
                        COEF_LEFT_button.config(text= str(rounded(NO_TIRE))+'%')
                        
                    else:
                        pass
                    

            
                if (show_camera):
                    amg = Image.fromarray(image)
                    amg = ImageTk.PhotoImage(image=amg)
                    heatmap_label.configure(image=amg)
                    heatmap_label.image = amg

                    frame = cv2.resize(img, (340, 340))  
                    cam = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    cam_label.config(image=cam)
                    cam_label.cam = cam

                    time.sleep(0.1)
                
                    if cv2.waitKey(1) == ord('q'):
                        break

                next_frame = now() + 100
        finally:
            if (runner):
            
                runner.stop()

def main_left(heatmap_label,cam_label,videoCaptureDeviceId):
    flatL_counter = 0
    tempL_counter = 0
    tempL_threshold = 4
    flatL_threshold = 4

    model = "modelfile2.eim"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)

    print('MODEL: ' + modelfile)

    with ImageImpulseRunner(modelfile) as runner:
        try:
            model_info = runner.init()
            print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
            labels = model_info['model_parameters']['labels']
            camera = cv2.VideoCapture(videoCaptureDeviceId)
            ret = camera.read()[0]
            if ret:
                backendName = camera.getBackendName()
                w = camera.get(3)
                h = camera.get(4)
                print("Camera %s (%s x %s) in port %s selected." %(backendName,h,w, videoCaptureDeviceId))
                camera.release()
            else:
                raise Exception("Couldn't initialize selected camera.")

            next_frame = 10 

            for res, img in runner.classifier(videoCaptureDeviceId):
                if (next_frame > now()):
                    time.sleep((next_frame - now()) / 1000)
                if "classification" in res["result"].keys():
                    FULL = res['result']['classification']['full']
                    FLAT = res['result']['classification']['flat']
                    NO_TIRE = res['result']['classification']['no_tire']
            
                    pixels = sensorL.readPixels()
                    pixels = [map(p, 27, 39, 0, COLORDEPTH - 1) for p in pixels]
                    bicubic = griddata(points, pixels, (grid_x, grid_y), method='cubic')
                    image = np.zeros((height, width, 3), dtype=np.uint8)
                    
                    for ix, row in enumerate(bicubic):
                        for jx, pixel in enumerate(row):
                            color = colors[constrain(int(pixel), 0, COLORDEPTH - 1)]
                            image[int(displayPixelHeight * ix):int(displayPixelHeight * (ix + 1)),
                                int(displayPixelWidth * jx):int(displayPixelWidth * (jx + 1))] = color
                    
                    avgL_temp = np.mean(sensorL.readPixels())
                    valueL_temp = int(rounded(avgL_temp))
                    TEMPERATURE1_button.config(text=f'{avgL_temp:.2f}°C')
                    if valueL_temp > 50 :
                        tempL_counter += 1
                        if tempL_counter >= tempL_threshold:
                            Alarm_SB.config(text="NORMAL")
                            Alarm_button.configure(bg="red")
                            Alarm_SB.configure(bg="red")
                            Alarm_SB.config(text="WARNING")
                            play_audio(suhu_file)
                            time.sleep(1)
                            Alarm_SB.config(text="NORMAL")
                            Alarm_SB.configure(bg="white")
                            Alarm_button.configure(bg="white")
                            tempL_counter = 0
                        
                    if FULL > 0.7:
                        CLASS_RIGHT_button.config(text='FULL')
                        CLASS_RIGHT_button.config(text= str(rounded(FULL))+'%')
                    elif FLAT > 0.8:
                        CLASS_RIGHT_button.config(text='FLAT')
                        COEF_RIGHT_button.config(text= str(rounded(FLAT))+'%')
                        flatL_counter += 1
                        if flatL_counter >= flatL_threshold:
                            Alarm_button.configure(bg="red")
                            Alarm_TB.config(text="WARNING")
                            Alarm_TB.configure(bg="red")
                            play_audio(kempis_file)
                            time.sleep(1)
                            Alarm_button.configure(bg="white")
                            Alarm_TB.config(text="NORMAL")
                            Alarm_TB.configure(bg="white")
                            flatL_counter = 0
                    elif NO_TIRE > 0.9:
                        CLASS_RIGHT_button.config(text='NO TIRE')
                        COEF_RIGHT_button.config(text= str(rounded(NO_TIRE))+'%')
                    else:
                        pass
                    
            
                if (show_camera):
                    amg = Image.fromarray(image)
                    amg = ImageTk.PhotoImage(image=amg)
                    heatmap_label.configure(image=amg)
                    heatmap_label.image = amg

                    frame = cv2.resize(img, (340, 340)) 
                    cam = ImageTk.PhotoImage(image=Image.fromarray(frame))
                    cam_label.config(image=cam)
                    cam_label.cam = cam

                    time.sleep(0.1)
                    #cv2.imshow('AFTD', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                    #cv2.imshow("AMG88xx Heatmap", image)
                    if cv2.waitKey(1) == ord('q'):
                        break

                next_frame = now() + 100
        finally:
            if (runner):
            
                runner.stop()

def now():
    return round(time.time() * 1000)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1440x900")  
    root.title("Jendela dengan Background Abu-abu")
    root.attributes('-fullscreen', True)
    
    root.bind('<Escape>', exit_fullscreen)
    
    frame = tk.Frame(root, bg="#424141")
    frame.place(relwidth=1, relheight=1) 

    canvas1 = tk.Canvas(frame, width=660, height=750, bg="#252222")
    canvas1.place(x=50, y=50) 

    canvas2 = tk.Canvas(frame, width=660, height=511, bg="#252222")
    canvas2.place(x=730, y=50) 

    canvas3 = tk.Canvas(frame, width=660, height=221, bg="#252222")
    canvas3.place(x=730, y=580)

    AFTD = tk.Label(frame, text="AUTOMATIC FLAT TIRE", font=("Verdana 30 bold"), bg="#252222", fg="white")
    AFTD.place(x=810, y=80) 

    DETECTION = tk.Label(frame, text="  DETECTION", font=("Verdana 30 bold"), bg="#252222", fg="white")
    DETECTION.place(x=920, y=130)

    TEMPERATURE1 = tk.Label(frame, text="RIGHT TEMP", font=("Verdana 14 bold"), bg="#252222", fg="white")
    TEMPERATURE1.place(x=770, y=510)
    
    TEMPERATURE1_button = tk.Button(root, text="0°C",font=("Verdana", 14))
    TEMPERATURE1_button.place(x=910, y=500)
    
    TEMPERATURE2 = tk.Label(frame, text="LEFT TEMP", font=("Verdana 14 bold"), bg="#252222", fg="white")
    TEMPERATURE2.place(x=1090, y=510)
    
    TEMPERATURE2_button = tk.Button(root, text="0°C",font=("Verdana", 14))
    TEMPERATURE2_button.place(x=1220, y=500)

    KONDISI_TB = tk.Label(frame, text="PRESURE", font=("Verdana 16 bold"), bg="#252222", fg="white")
    KONDISI_TB.place(x=800, y=620)
    
    KONDISI_TB1 = tk.Label(frame, text="CONDITION", font=("Verdana 16 bold"), bg="#252222", fg="white")
    KONDISI_TB1.place(x=790, y=650)
    
    Alarm_TB = tk.Button(root, text="NORMAL", width=5, height=2)
    Alarm_TB.place(x=825, y=700)

    KONDISI_SB = tk.Label(frame, text="TEMPERATURE", font=("Verdana 16 bold"), bg="#252222", fg="white")
    KONDISI_SB.place(x=960, y=620)
    
    KONDISI_SB1 = tk.Label(frame, text="CONDITION", font=("Verdana 16 bold"), bg="#252222", fg="white")
    KONDISI_SB1.place(x=985, y=650)

    Alarm_SB = tk.Button(root, text="NORMAL", width=5, height=2)
    Alarm_SB.place(x=1015, y=700)

    CAM1 = tk.Label(frame, text=" RIGHT", font=("Verdana 24 bold"), bg="#252222", fg="white")
    CAM1.place(x=520, y=130)

    CAM11 = tk.Label(frame, text="CAMERA", font=("Verdana 24 bold"), bg="#252222", fg="white")
    CAM11.place(x=510, y=170) 
    
    CLASS_RIGHT = tk.Label(frame, text="Class", font=("Verdana 16 bold"), bg="#252222", fg="white")
    CLASS_RIGHT.place(x=490, y=250)  

    CLASS_RIGHT_button = tk.Button(root, text="NONE",font=("Verdana", 12))
    CLASS_RIGHT_button.place(x=580, y=250)
    
    COEF_RIGHT = tk.Label(frame, text="Confidence", font=("Verdana 16 bold"), bg="#252222", fg="white")
    COEF_RIGHT.place(x=460, y=330) 

    COEF_RIGHT_button = tk.Button(root, text="0%",font=("Verdana", 12))
    COEF_RIGHT_button.place(x=600, y=330)
   
    CAM2 = tk.Label(frame, text="  LEFT", font=("Verdana 24 bold"), bg="#252222", fg="white")
    CAM2.place(x=510, y=470)  

    CAM22 = tk.Label(frame, text="CAMERA", font=("Verdana 24 bold"), bg="#252222", fg="white")
    CAM22.place(x=500, y=510)
    
    CLASS_LEFT = tk.Label(frame, text="Class", font=("Verdana 16 bold"), bg="#252222", fg="white")
    CLASS_LEFT.place(x=490, y=600)  

    CLASS_LEFT_button = tk.Button(root, text="NONE",font=("Verdana", 12))
    CLASS_LEFT_button.place(x=580, y=600)

    COEF_LEFT = tk.Label(frame, text="Confidence", font=("Verdana 16 bold"), bg="#252222", fg="white")
    COEF_LEFT.place(x=460, y=680)  
    
    COEF_LEFT_button = tk.Button(root, text="0%",font=("Verdana", 12))
    COEF_LEFT_button.place(x=600, y=680)

  
    camera_label1 = tk.Label(frame)
    camera_label1.place(x=80, y=80)  

    heatmap_label1 = tk.Label(frame)
    heatmap_label1.place(x=760, y=210)

    camera_label2 = tk.Label(frame)
    camera_label2.place(x=80, y=430)  

    heatmap_label2 = tk.Label(frame)
    heatmap_label2.place(x=1070, y=210)
    
    def toggle_alarm_color():
        global alarm_on 
        if alarm_on:
            Alarm_button.configure(bg="white")
        else:
            Alarm_button.configure(bg="red")
            print("Alarm ON")
            play_audio(alarm_file)
        alarm_on = not alarm_on

    def alarm_button_click():
        toggle_alarm_color() 
        
    Alarm_button = tk.Button(root, text="ALARM", width=20, height=7,command=alarm_button_click)
    Alarm_button.place(x=1170, y=620)
    
    alarm_on = False

    def LEFT():
        left_thread = threading.Thread(target=main_left, args=(heatmap_label1,camera_label1,0))
        left_thread.daemon = True
        left_thread.start()
    def RIGHT():
        right_thread = threading.Thread(target=main_right, args=(heatmap_label2,camera_label2,1))
        right_thread.daemon = True
        right_thread.start()
    
    
    LEFT()
    RIGHT()
    
    root.mainloop()
  
  
