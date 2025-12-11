import cv2
import numpy as np
from picamera2 import Picamera2
import time
import serial

# Ouverture du port série
ser = serial.Serial('/dev/ttyACM1', 115200, timeout=1)
time.sleep(2)


def empty(a):
    pass


# Trackbars
cv2.namedWindow('image')
cv2.createTrackbar('H min', 'image', 0, 179, empty)
cv2.createTrackbar('H max', 'image', 19, 179, empty)
cv2.createTrackbar('S min', 'image', 110, 255, empty)
cv2.createTrackbar('S max', 'image', 240, 255, empty)
cv2.createTrackbar('V min', 'image', 153, 255, empty)
cv2.createTrackbar('V max', 'image', 255, 255, empty)


def sketch(image, h_min, h_max, s_min, s_max, v_min, v_max):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv_image, lower, upper)
    imgResult = cv2.bitwise_and(image, image, mask=mask)

    # Contours
    ret, thresh = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cx = cy = None

    if contours:
        largest = max(contours, key=cv2.contourArea)

        # Filtre les objets trop petits
        if cv2.contourArea(largest) < 500:
            return imgResult, None, None

        cv2.drawContours(imgResult, [largest], -1, (0, 255, 0), 2)

        M = cv2.moments(largest)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            cv2.circle(imgResult, (cx, cy), 7, (0, 0, 255), -1)
            cv2.putText(
                imgResult,
                f"({cx},{cy})",
                (cx + 10, cy),
                
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )

    return imgResult, cx, cy


# Camera Raspberry
picam = Picamera2()
picam.preview_configuration.main.format = "XRGB8888"
picam.configure("preview")
picam.start()


frame_width = 640
frame_height = 480
cx_center = frame_width // 2
cy_center = frame_height // 2

# --- FOV ---
HFOV = 54
VFOV = 54
deg_per_px_x = HFOV / frame_width
deg_per_px_y = VFOV / frame_height

# --- Positions initiales moteurs ---
pan = 90
tilt = 90

while True:
    frame = picam.capture_array()

    # Trackbars
    h_min = cv2.getTrackbarPos('H min', 'image')
    h_max = cv2.getTrackbarPos('H max', 'image')
    s_min = cv2.getTrackbarPos('S min', 'image')
    s_max = cv2.getTrackbarPos('S max', 'image')
    v_min = cv2.getTrackbarPos('V min', 'image')
    v_max = cv2.getTrackbarPos('V max', 'image')

    result, cx, cy = sketch(frame, h_min, h_max, s_min, s_max, v_min, v_max)
    
    if cx is not None:
        # Erreur en pixels
        error_x = cx - cx_center   # droite = positif
        error_y = cy - cy_center   # bas = positif

        # Conversion pixels → degrés
        delta_pan = error_x * deg_per_px_x *0.1  # signe inversé
        delta_tilt = -error_y * deg_per_px_y *0.1 # signe inversé

        # Mise à jour des angles
        pan += delta_pan
        tilt += delta_tilt

        # Clamping
        pan = max(0, min(180, pan))
        tilt = max(0, min(180, tilt))

        # Envoi à l’Arduino
        if (abs(pan - last_pan) > 0.5 or abs(tilt - last_tilt) > 0.5) and (time.time() - last_send_time > SEND_INTERVAL):
            ser.write(f"PAN:{pan}\n".encode())
            ser.write(f"TILT:{tilt}\n".encode())
            last_send_time = time.time()
            last_pan = pan
            last_tilt = tilt

    cv2.imshow('Camera', result)

    if cv2.waitKey(1) == 13:  # touche ENTER
        break

picam.stop()
picam.close()
cv2.destroyAllWindows()
ser.close()
