import numpy as np
import cv2
import time
import car_control as cc

gBlur = (5, 5)
min_thre = 75
width = 1280//2
height = 720//2

def inv(x):
    if(x == 1):
        x = 0
    else:
        x = 1
    return x


def setMotorDir(reg, m1, m2, m3, m4):
    #reg.set_by_list([0, 0, 1, 0, 0, 1, 1, 1])
    reg.set_by_list([inv(m3), inv(m4), m3, m2, m2, inv(m1), inv(m2), m4])

def move(reg, dir, fd, m1, m2, m3, m4):
    if(fd):
        setMotorDir(reg, 1, 1, 1, 1)
        if(dir):
            GPIO.output(m1, GPIO.HIGH)
            GPIO.output(m2, GPIO.LOW)
            GPIO.output(m3, GPIO.LOW)
            GPIO.output(m4, GPIO.HIGH)
        else:
            GPIO.output(m1, GPIO.LOW)
            GPIO.output(m2, GPIO.HIGH)
            GPIO.output(m3, GPIO.HIGH)
            GPIO.output(m4, GPIO.LOW)
    else:
        GPIO.output(m1, GPIO.HIGH)
        GPIO.output(m2, GPIO.HIGH)
        GPIO.output(m3, GPIO.HIGH)
        GPIO.output(m4, GPIO.HIGH)
        if(dir):
            setMotorDir(reg, 0, 1, 1, 0)
        else:
            setMotorDir(reg, 1, 0, 0, 1)

# def setPWM(pin, pwm): 
#     ts = time.time()
#     for i in range(3):
#         if time.time() - ts < pwm/1000:
#             GPIO.output(pin, GPIO.HIGH)

#         GPIO.output(pin, GPIO.LOW)
#         time.sleep(0.1 - pwm/1000)

def motor_stop(m1, m2, m3, m4):
    GPIO.output(m1, GPIO.LOW)
    GPIO.output(m2, GPIO.LOW)
    GPIO.output(m3, GPIO.LOW)
    GPIO.output(m4, GPIO.LOW)


def gstreamer_pipeline(
    capture_width=width,
    capture_height=height,
    display_width=width,
    display_height=height,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def processing_image(img):

    # img control
    img = img[height//3:height,:]
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # blur = cv2.GaussianBlur(gray, gBlur, 0)
    thresh = cv2.threshold(gray, min_thre, 255, cv2.THRESH_BINARY_INV)[1]

    contours,_= cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
    mainContour = max(contours, key = cv2.contourArea)
    M = cv2.moments(mainContour)
    if M['m00'] != 0:#не получается деление на ноль (т.е. если получен хотя-бы один контур)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        return cx, cy
    return 0, 0

def move_control(img_x, img_y, goal_x, goal_y):
    if goal_x >= img_x:
        return 1
    return 0

def detected_green(img):
    # img = img[height-1:height,:]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv_min = np.array((36, 71, 62), np.uint8)
    hsv_max = np.array((139, 140, 153), np.uint8)
    thresh = cv2.inRange(hsv, hsv_min, hsv_max)
    moments = cv2.moments(thresh, 1)
    area = moments['m00']
    # print(area)
    if area > tresh_hole:
        return True
    return False

red_line = False
green_line = False
sign_clutch = False

tresh_hole = 5000

GPIO.setmode(GPIO.BOARD)
shift_register = pi74HC595()

MOTOR_PWM_1 = 24
MOTOR_PWM_2 = 23
MOTOR_PWM_3 = 21
MOTOR_PWM_4 = 22

MOTOR_EN = 12

GPIO.setup(MOTOR_EN, GPIO.OUT)
GPIO.setup(MOTOR_PWM_1, GPIO.OUT)
GPIO.setup(MOTOR_PWM_2, GPIO.OUT)
GPIO.setup(MOTOR_PWM_3, GPIO.OUT)
GPIO.setup(MOTOR_PWM_4, GPIO.OUT)

GPIO.output(MOTOR_EN, GPIO.LOW)

cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

if __name__ == "__main__":

    # first green line
    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if detected_green(frame):
                    print("green detected")
                    move(shift_register, inv(dir), 2, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
                    time.sleep(0.15)
                    GPIO.output(MOTOR_PWM_1, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_2, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_3, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_4, GPIO.LOW)
                                
                    break
                dir = move_control(frame_x, frame_y, goal_x, goal_y)
                move(shift_register, inv(dir), 1, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
            else:
                break
    
    start_time = time.time()

    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if time.time() - start_time > 0.01:
                    break
                move(shift_register, 1, 0, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)

    GPIO.output(MOTOR_PWM_1, GPIO.LOW)
    GPIO.output(MOTOR_PWM_2, GPIO.LOW)
    GPIO.output(MOTOR_PWM_3, GPIO.LOW)
    GPIO.output(MOTOR_PWM_4, GPIO.LOW)

    # detected sign clutch
    # while True:
    #     pass
    time.sleep(10)
    print("move")

    # second green line
    start_time = time.time()

    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if time.time() - start_time > 2:
                    if detected_green(frame):
                        print("green detected")
                        move(shift_register, inv(dir), 2, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
                        time.sleep(0.15)
                        GPIO.output(MOTOR_PWM_1, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_2, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_3, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_4, GPIO.LOW)        
                        break
                dir = move_control(frame_x, frame_y, goal_x, goal_y)
                move(shift_register, inv(dir), 1, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
            else:
                break
    
    start_time = time.time()

    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                print(frame_x - goal_x)
                print(time.time() - start_time)
                if abs(frame_x - goal_x) < 100 and time.time() - start_time > 0.1:
                    break
                move(shift_register, 1, 0, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)

    GPIO.output(MOTOR_PWM_1, GPIO.LOW)
    GPIO.output(MOTOR_PWM_2, GPIO.LOW)
    GPIO.output(MOTOR_PWM_3, GPIO.LOW)
    GPIO.output(MOTOR_PWM_4, GPIO.LOW)

    # detected sign clutch
    # while True:
    #     pass
    time.sleep(10)
    print("move")

    # 180
    start_time = time.time()

    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if abs(frame_x - goal_x) < 100 and time.time() - start_time > 1.1:
                    break
                if goal_x - frame_x > 0:
                    a = 1
                a = 0
                move(shift_register, a, 0, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)

    GPIO.output(MOTOR_PWM_1, GPIO.LOW)
    GPIO.output(MOTOR_PWM_2, GPIO.LOW)
    GPIO.output(MOTOR_PWM_3, GPIO.LOW)
    GPIO.output(MOTOR_PWM_4, GPIO.LOW)

    # go home

# first green line
    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if detected_green(frame):
                    print("green detected")
                    move(shift_register, inv(dir), 2, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
                    time.sleep(0.15)
                    GPIO.output(MOTOR_PWM_1, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_2, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_3, GPIO.LOW)
                    GPIO.output(MOTOR_PWM_4, GPIO.LOW)
                                
                    break
                dir = move_control(frame_x, frame_y, goal_x, goal_y)
                move(shift_register, inv(dir), 1, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
            else:
                break

    # second green line
    start_time = time.time()

    while True:
            ret, frame = cap.read()
            if ret:
                frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
                try:  
                    goal_x, goal_y = processing_image(frame)
                except:
                    continue
                if time.time() - start_time > 2:
                    if detected_green(frame):
                        print("green detected")
                        move(shift_register, inv(dir), 2, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
                        time.sleep(0.15)
                        GPIO.output(MOTOR_PWM_1, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_2, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_3, GPIO.LOW)
                        GPIO.output(MOTOR_PWM_4, GPIO.LOW)        
                        break
                dir = move_control(frame_x, frame_y, goal_x, goal_y)
                move(shift_register, inv(dir), 1, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)
            else:
                break

    # start_time = time.time()

    # while True:
    #         ret, frame = cap.read()
    #         if ret:
    #             frame_x, frame_y = frame.shape[1]//2, frame.shape[0]//2
    #             try:  
    #                 goal_x, goal_y = processing_image(frame)
    #             except:
    #                 continue

    #             if abs(frame_x - goal_x) < 100 and time.time() - start_time > 0.1:
    #                 break
    #             if goal_x - frame_x > 0:
    #                 a = 1
    #             a = 0
    #             move(shift_register, a, 0, MOTOR_PWM_1, MOTOR_PWM_2, MOTOR_PWM_3, MOTOR_PWM_4)

    # GPIO.output(MOTOR_PWM_1, GPIO.LOW)
    # GPIO.output(MOTOR_PWM_2, GPIO.LOW)
    # GPIO.output(MOTOR_PWM_3, GPIO.LOW)
    # GPIO.output(MOTOR_PWM_4, GPIO.LOW)
