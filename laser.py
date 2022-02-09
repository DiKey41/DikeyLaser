import numpy as np
import cv2


cap = cv2.VideoCapture(0)


while(True):
    ret, frame = cap.read()
    #cv2.imshow('Frame',frame)
    frameCopy=frame.copy()
    
    
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    hsv = cv2.blur(hsv,(5,5))
    mask = cv2.inRange(hsv,(135,208,102),(249,243,186))
    #cv2.imshow('Mask',mask)


    mask=cv2.erode(mask, None, iterations = 2)
    mask=cv2.dilate(mask, None, iterations = 4)
    cv2.imshow('Mask2',mask)
    
    
    
    contours = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    contours = contours[0]
    if contours:
        contours = sorted(contours,key=cv2.contourArea,reverse=True)
        cv2.drawContours(frame,contours,0,(255,0,255),3)
        #cv2.imshow('Contours',frame)
    
        (x,y,w,h) = cv2.boundingRect(contours[0])
        cv2.rectangle(frame,(x,y),((x+w),(y+h)),(0,255,0),2)
        cv2.imshow('Rectangle',frame)
        
        roImg=frameCopy[y:y+h,x:x+w]
        cv2.imshow('Detect',roImg)
        roImg=cv2.resize(roImg,(64,64))
        roImg=cv2.inRange(roImg,(89,124,73),(255,255,255))
        thresh = cv2.inRange(hsv, hsv_min, hsv_max)
        moments = cv2.moments(thresh, 1)
        area = moments['m00']
        print(area)
        if area > tresh_hole:
            return True
        return False
        
    

        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
