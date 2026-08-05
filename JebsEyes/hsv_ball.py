import cv2
import numpy as np
import math

LOWER_GREEN = np.array([25, 80, 80])
UPPER_GREEN = np.array([40, 255, 255])

MIN_AREA = 300
MAX_AREA = 50000
CIRCULARITY_THRESHOLD = 0.65

def clean_mask(mask):
    """Cleans up a binary HSV mask to remove noise and false positives."""
    # Note: Removed cv2.imshow from this thread to prevent window manager locks.
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def detect_tennis_ball_via_colour(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
    mask = clean_mask(mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    best_contour = None
    best_score = 0

    for c in contours:
        area = cv2.contourArea(c)
        if area < MIN_AREA or area > MAX_AREA:
            continue

        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue

        circularity = 4 * math.pi * area / (perimeter * perimeter)

        if circularity > CIRCULARITY_THRESHOLD:
            if circularity > best_score:
                best_score = circularity
                best_contour = c

    if best_contour is None:
        return None

    (x, y), radius = cv2.minEnclosingCircle(best_contour)

    return {
        "name": "tennis_ball",
        "x": int(x),
        "y": int(y),
        "size": int(radius),
        "confidence": float(best_score)
    }