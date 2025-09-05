#####################################################################
#
#   Driver for JGB37-520 motorisation
#      V1 - same speed_control_output for both motors
#           (see BalanceCar function)
#      html_file = index_dmpTumbllrV1.html -> gain tuning
#                  tumbllr_joystick.html -> fun !
#
#####################################################################
import os, socket, network, websocket_helper

import os, socket, network, websocket_helper
from websocket import websocket
from WifiConnect import WifiConnect

from machine import Pin, PWM, Timer
from MPU6050dmp20 import *
from time import sleep_ms

#
html_file = '/SBR/PID_tuning.html'
# html_file = '/SBR/joystick.html'
#
def notify(s):
    ''' websocket handler'''
    global kp, kd, kps, kis, speed, turn
    try:
        msg = ws.read()
        exec(msg)
        print(msg.decode().strip())
    except:
        pass

def serve_page(sock):
    ''' send webserver page '''
    try:
        sock.sendall('HTTP/1.1 200 OK\nConnection: close\nServer: WebSocket Server\nContent-Type: text/html\n')
        length = os.stat(html_file)[6]
        sock.sendall('Content-Length: {}\n\n'.format(length))
        # Process page by lines to avoid large strings
        with open(html_file, 'r') as f:
            for line in f:
                sock.sendall(line)
    except OSError:
        print('*** serve_page : error sending index.html')

def dataReadyInt(p):
    ''' IMU handler '''
    global new_data

    if mpu.getFIFOCount() != 42:
        mpu.resetFIFO()
        new_data = False
        return
    buf = mpu.getFIFOBytes(42)
    q = mpu.dmpGetQuaternion(buf)
    gx, gy, gz = mpu.dmpGetGravity(q)
    try:
        mpu.thetay = atan(gx / (gy**2 + gz**2))*57.3
    except:
        pass
    mpu.omy = -unpack('>h', buf[20:22])[0]
    mpu.omz = unpack('>h', buf[24:26])[0]
    new_data = True

def constrain(val, min, max):
    if val > max:
        return max
    elif val < min:
        return min
    else:
        return val

def start():
    ''' rise up '''
    global balancing
    global encoder_count_left, encoder_count_right
    global speed_control_period_count
    global speed_filter, car_speed_integral, speed, turn
    global speed_cmd, turn_cmd
    global speed_control_output, rotation_control_output, balance_control_output
    
    if balancing: return
    # reset control variables
    encoder_count_left, encoder_count_right = 0, 0
    speed_control_period_count = 0
    speed_filter, car_speed_integral, speed, turn = 0, 0, 0, 0
    speed_cmd, turn_cmd = 0, 0
    speed_control_output, rotation_control_output = 0, 0
    dir = mpu.thetay > MAX_ANGLE 
    pin1r.value(dir)
    pin2r.value(not dir)
    pin1l.value(dir)
    pin2l.value(not dir)
    mr.duty_u16(32768)
    ml.duty_u16(32768)
    sleep_ms(200)
    balancing = True

def down():
    ''' lay down '''
    global balancing
    
    if not balancing: return
    mr.duty_u16(0)
    ml.duty_u16(0)
    sleep_ms(2000)
    balancing = False
    
def inc_enc_right(p):
    ''' right encoder handler '''
    global encoder_count_right
    encoder_count_right += -1 if pin2r.value() else 1

def inc_enc_left(p):
    ''' left encoder handler '''
    global encoder_count_left
    encoder_count_left += -1 if pin2l.value() else 1

def BalanceCar(t):
    ''' balance and speed control '''
    global encoder_count_left, encoder_count_right
    global pwm_left, pwm_right, speed_control_period_count
    global speed_filter, car_speed_integral, speed, turn
    global speed_cmd, turn_cmd
    global speed_control_output, rotation_control_output, balance_control_output
    global acc
    
    if not balancing: return
    if not new_data: mpu.thetay += mpu.omy * 0.005
    balance_control_output = -kp * mpu.thetay - kd * mpu.omy # balance control every 5ms
    
    speed_control_period_count += 1
    if speed_control_period_count >= 8:   # speed control every 40ms
        speed_control_period_count = 0
        car_speed = (encoder_count_left + encoder_count_right) * 0.5
        encoder_count_left = 0
        encoder_count_right = 0
        speed_filter = speed_filter * 0.7 + car_speed * 0.3
        speed_cmd = speed
        turn_cmd = turn
        acc = speed_cmd - speed_filter
        car_speed_integral += constrain(acc, -MAX_ACC, MAX_ACC)
        speed_control_output = -kps * speed_filter + kis * car_speed_integral
        rotation_control_output = turn
     
    pwm_left = int((balance_control_output - speed_control_output + rotation_control_output) * 256)
    pwm_right = int((balance_control_output - speed_control_output - rotation_control_output) * 256)
    pwm_right += 0 if pwm_right > 0 else -500  # account for left-right motor asymetry
    pwm_left = constrain(pwm_left, -65535, 65535)
    pwm_right = constrain(pwm_right, -65535, 65535)

    if pwm_left > 0:
        pin1l.on()
        pin2l.off()
    else:
        pin1l.off()
        pin2l.on()
    ml.duty_u16(abs(pwm_left))
    
    if pwm_right > 0:
        pin1r.on()
        pin2r.off()
    else:
        pin1r.off()
        pin2r.on()
    mr.duty_u16(abs(pwm_right))
    
#  Communication
print('WifiConnect successfull, ip =', WifiConnect('my_SSID').ifconfig()[0])

listen_s = socket.socket()
listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

ai = socket.getaddrinfo("0.0.0.0", 80)
addr = ai[0][4]
listen_s.bind(addr)
listen_s.listen(1)

ws_ok = False

while not ws_ok:
    client, remote_addr = listen_s.accept()
    try:
        websocket_helper.server_handshake(client)
        ws = websocket(client, True)
        client.setblocking(False)
        client.setsockopt(socket.SOL_SOCKET, 20, notify)
        ws_ok = True
    except OSError:
        serve_page(client)
        client.close()

# constants
kp  = 30
kd  = 2.6
kps = 5
kis = 0.15

MAX_ANGLE        = 20.
MAX_START_ANGLE  = 5.
MAX_ACC          = 40

# IMU init
i2c = SoftI2C(scl=Pin(9),sda=Pin(8),freq=400_000)
mpu = MPU6050dmp(i2c, axOff=-3606, ayOff=-922, azOff=1235, gxOff=-156, gyOff=25, gzOff=98)
intPin = Pin(7, Pin.IN)
mpu.dmpInitialize()
mpu.setDMPEnabled(True)
mpu.getIntStatus()
mpu.resetFIFO()
intPin.irq(dataReadyInt, Pin.IRQ_FALLING)
mpu.thetay, mpu.omy = 0, 0
sleep_ms(1000)

# motors init
mr = PWM(Pin(13))
mr.freq(500)
pwm_right = 0
mr.duty_u16(0) # duty offset right = 12000
pin1r = Pin(14, Pin.OUT)
pin2r = Pin(15, Pin.OUT)
ml = PWM(Pin(16))
ml.freq(500)
pwm_left = 0
ml.duty_u16(0) # duty offset left = 12000
pin1l = Pin(17, Pin.OUT)
pin2l = Pin(18, Pin.OUT)

# encoders init
en1r = Pin(11, Pin.IN)
encoder_count_right = 0
en1r.irq(inc_enc_right, Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)
en1l = Pin(19, Pin.IN)
encoder_count_left = 0
en1l.irq(inc_enc_left, Pin.IRQ_FALLING | Pin.IRQ_RISING, hard=True)

# board led init
led = Pin("LED", Pin.OUT)

balancing = False
speed, turn = 0, 0
tim = Timer(period=5, callback=BalanceCar)  # balance control every 5ms

# main loop
while True:
    try:
        Pin("LED", Pin.OUT).on()
        while abs(mpu.thetay) > MAX_START_ANGLE:
            sleep_ms(10)
        Pin("LED", Pin.OUT).off()
        
        # reset control variables
        encoder_count_left, encoder_count_right = 0, 0
        speed_control_period_count = 0
        speed_filter, car_speed_integral, speed, turn = 0, 0, 0, 0
        speed_cmd, turn_cmd = 0, 0
        speed_control_output, rotation_control_output = 0, 0
        balancing = True
        
        while abs(mpu.thetay) < MAX_ANGLE:
            # send data to web client
            sleep_ms(300)
            msg = 'acc:{:5.0f},integ:{:5.0f}'.format(acc, car_speed_integral)
            ws.write(msg.encode())
        
        balancing = False
        mr.duty_u16(0)
        ml.duty_u16(0)
        
    except KeyboardInterrupt:
        balancing = False
        tim.deinit()
        mr.duty_u16(0)
        ml.duty_u16(0)
        break
 