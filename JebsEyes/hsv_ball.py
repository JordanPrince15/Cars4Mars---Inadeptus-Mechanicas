import cv2
import numpy as np
import math

LOWER_GREEN = np.array([25, 80, 80])
UPPER_GREEN = np.array([40, 255, 255])

MIN_AREA = 500

def clean_mask(mask):
    """
    Cleans up a binary HSV mask to remove noise and false positives
    """
    # Shows us the mask:
    cv2.imshow("Mask", mask)
    cv2.waitKey(1)

    # 1. Smooth the mask to remove salt-and-pepper noise
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # 2. Morphological opening (remove small noise)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 3. Morphological closing (fill holes inside ball)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask

def detect_tennis_ball_via_colour(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
    mask = clean_mask(mask)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None   # <-- CRITICAL SAFETY CHECK

    best_contour = None
    best_score = 0

    for c in contours:
        if not is_ball_contour(c):
            continue

        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        circularity = 4 * math.pi * area / (perimeter * perimeter + 1e-5)

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


def is_ball_contour(contour, min_area=300, max_area=50000):
    area = cv2.contourArea(contour)
    if area < min_area or area > max_area:
        return False

    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return False

    circularity = 4 * math.pi * area / (perimeter * perimeter)

    # Tennis balls are close to circular
    return circularity > 0.65