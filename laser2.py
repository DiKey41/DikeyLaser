import numpy as np
import cv2


cap = cv2.VideoCapture(0)

while(True): 
  
  
    ret, frame = cap.read()
    # success, frame_read = cap.read()
    frame = frame[100:720, 0:1280]
    img = cv2.resize(frame, (width, height))
    img = cv2.rotate(img, cv2.ROTATE_180)
    img = cv2.flip(img, 1)
    imgContour = img.copy()
    imgHsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    h_min = 152
    h_max = 220
    s_min = 182
    s_max = 245
    v_min = 108
    v_max = 255

    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(imgHsv, lower, upper)
    result = cv2.bitwise_and(img, img, mask=mask)
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    imgBlur = cv2.GaussianBlur(result, (7, 7), 1)
    imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Frame',imgGray)
