from astropy.io import fits
import numpy as np
import os
import subprocess
import serial
import serial.tools.list_ports
import io
import datetime
import time
import json
import matplotlib.pyplot as plt
from tkinter import *
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
#Take multiple exposures and stack them, normalize them
#Set framerate to 10Hz, take exposures up to set exptime


window = Tk()
window.geometry('1000x800')
window.grid()

savepath = None
imgname = None

def connect():
    #Connects to the camera via pyserial, returns the serial object and port
    ser = None
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if 'C-RED 2' in port.description:
            print(port.description)
            connection_port = port.description.split('(')[1].split(')')[0]
    retry = 20
    try_ = 0
    while try_ <= retry:
        try:
            ser = None
            ser = serial.Serial(connection_port, timeout=3)
            if ser:
                print(f'Successfully connected to port {connection_port}')
                break
        except:
            try_ += 1
            print('Could not connect to CRED2 Camera, retrying')
            time.sleep(1)
    return ser, connection_port


ser, portnumber = connect()
conn = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
ser.parity = 'N'
ser.bytesize = 8
ser.baudrate = 115200
ser.stopbits = 1


def read_output(conn, wait=3):
    var = 0
    lines = list()
    while var<=wait:
        print(conn.readline())
        lines.append(conn.readline())
        var += 1
        if len(lines) >= 2:
            if len(lines[len(lines) -1]) == 0:
                var = wait
                break

def raw_expose(sdkloc, n, output_dir, filename):
    #Sends the command to the camera to expose and save the image
    cmd = '"' + sdkloc + '"' + " -n" + str(n) + " " + r'"' + str(output_dir) + str(filename) + r'"'
    print(cmd)
    subprocess.run(cmd, shell=True, check=True)
    print('After cmd')

def clear_canvas(canvas):
    #Clears tkinter image display
    canvas.get_tk_widget().pack_forget()

def convert_raw_single(n, x, y, input_dir, input_name, output_dir, output_name):
#    cmd = "n" + "x" + "y" + str(input_dir) + str(input_name) + str(output_dir) + str(output_name)
    full_input_name = str(input_dir) + str(input_name)
    print(full_input_name)
    print('In convert_raw_single')
    with open(full_input_name, "rb") as f:

        img=np.zeros((y,x),dtype=int)
        cube = np.zeros((y,x,n),dtype=int)

        for i in range(0,y):
            for j in range(0,x):
                for k in range(0,n):
                    twobyte = f.read(2)
                    pixelintensity= int.from_bytes(twobyte,byteorder='little',signed=False)
                    #print(i,j,pixelintensity)
                    img[i,j] = img[i,j] + pixelintensity
                    cube[i,j,k] = pixelintensity
                    hdr=fits.Header()

    hdr['author'] = 'Owen'

    # makes fits data array
    hdu = fits.PrimaryHDU(img,header=hdr)

    full_output_name = str(input_dir) + str(output_name)
    print(full_output_name)
    # writes it out
    hdu.writeto(full_output_name, overwrite=True)

    return img

def expose():
    global canvas
    if ser:
        with ser:
            conn = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            ser.parity='N'
            ser.bytesize=8
            ser.baudrate=115200
            ser.stopbits=1

            print(f'Port is open: {ser.isOpen()}')

            with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json') as f:
                config = json.load(f)

            xxx = 0
            for n in range(0, int(config['N_Images'])):

                #imgpath = os.path.join(r"C:/Users/GMU Observtory1/Desktop/CRED2 Stuff", "TestImages/")
                imgpath = config['Save_Dir']
                timepath = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                image = f"{config['Filename']}-{xxx}.raw"
                fitsimage = f"{config['Filename']}-{xxx}.fits"

                temp = os.path.join(config['Save_Dir'], image)
                save_path = os.path.split(temp)[0] + "\\"
                print(save_path)

                sdkloc = r"C:\Program Files\First Light Imaging\SDK\bin\usb_sdk_demo.exe"
                sdkdir = os.path.dirname(sdkloc)


                raw_expose(sdkloc, 1, save_path, image)
                print(f"Exposing image {xxx} out of {config['N_Images']}")
                data = convert_raw_single(1, 640, 512, save_path, image,  "", fitsimage)
                ser.reset_input_buffer()
                #SendCommand_('shutdown')
                xxx += 1

                try:
                    clear_canvas(canvas)
                except:
                    pass
                fig = None
                fig = Figure(figsize=(5, 5),
                             dpi=100)
                # adding the subplot
                plot1 = fig.add_subplot(111)
                # plotting the graph
                plot1.imshow(data, cmap='viridis')
                # creating the Tkinter canvas
                # containing the Matplotlib figure
                canvas = FigureCanvasTkAgg(fig,
                                           master=window)
                canvas.draw()
                # placing the canvas on the Tkinter window
                canvas.get_tk_widget().grid(row=15, column=1)
                # creating the Matplotlib toolbar

                # placing the toolbar on the Tkinter window
                #canvas.get_tk_widget().pack()

    def set_tint(t):
        io.flush()
        io.write(b"set tint\n".decode("utf-8", "ignore"))
        io.flush()
        return t


def save_set():
    savepath_ = savepath_entry.get()
    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json') as f:
        config = json.load(f)

    config['Save_Dir'] = savepath_

    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def name_set():
    fname = filename_entry.get()
    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json') as f:
        config = json.load(f)

    config['Filename'] = fname

    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def n_set():
    n_images = n_images_entry.get()
    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json') as f:
        config = json.load(f)

    config['N_Images'] = n_images

    with open('H:\Observatory Files\Testing\CRED2 Stuff\config.json', 'w') as f:
        f.write(json.dumps(config, indent=4))


def SendCommand_(command_to_send):
    command = command_to_send.encode()
    print(command_to_send)
    conn.write((b"%b \n" %command).decode("utf-8", "ignore"))
    conn.flush()
    #read_output(conn, wait=wait)

def t_int_set():
    exp = exp_entry.get()
    SendCommand_(f'set tint {int(exp)}')

plot_button = Button(master = window, command = expose, height = 2, width = 10, text = "Expose")
exp_entry = tk.Entry(window)
exp_set = Button(master=window, height=1, width=5, text='Set')
tk.Label(window, text='Exposure Time').grid(row=5, column=3)

savepath_entry = tk.Entry(window)
savepath_set = Button(master=window, height=1, width=5, text='Set', command=save_set)
tk.Label(window, text='Image Directory:').grid(row=10, column=3)

filename_entry = tk.Entry(window)
filename_set = Button(master=window, height=1, width=5, text='Set', command=name_set)
tk.Label(window, text='Filename:').grid(row=11, column=3)

n_images_entry = tk.Entry(window)
n_images_set = Button(master=window, height=1, width=5, text='Set', command=n_set)
tk.Label(window, text='Number of Images:').grid(row=6, column=3)

# place the button
# into the window
plot_button.grid(row=6, column=1)
exp_set.grid(row=5, column=5)
exp_entry.grid(row=5, column=4)
n_images_entry.grid(row=6, column=4)
n_images_set.grid(row=6, column=5)
savepath_entry.grid(row=10, column=4)
savepath_set.grid(row=10, column=5)
filename_entry.grid(row=11, column=4)
filename_set.grid(row=11, column=5)

window.mainloop()


