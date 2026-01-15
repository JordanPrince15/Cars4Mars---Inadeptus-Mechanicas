import cv2
import numpy as np

class TennisBallDetector:
    def __init__(self, lower_green=None, upper_green=None, min_area=500, min_radius=10):
        """
        Initialize the tennis ball detector.
        Args:
            lower_green: np.array of HSV lower bound
            upper_green: np.array of HSV upper bound
            min_area: minimum contour area to consider
            min_radius: minimum radius of enclosing circle
        """
        self.LOWER_GREEN = lower_green if lower_green is not None else np.array([25, 80, 80])
        self.UPPER_GREEN = upper_green if upper_green is not None else np.array([40, 255, 255])
        self.min_area = min_area
        self.min_radius = min_radius

    def detect(self, frame):
        """
        Detect tennis ball in a given frame.
        Args:
            frame: BGR image (numpy array)
        Returns:
            dict with x, y, size OR None if not found
        """
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create mask
        mask = cv2.inRange(hsv, self.LOWER_GREEN, self.UPPER_GREEN)

        # Clean up noise
        mask = cv2.GaussianBlur(mask, (11, 11), 0)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Largest green object
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)

            if area > self.min_area:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                if radius > self.min_radius:
                    return {
                        "x": int(x),
                        "y": int(y),
                        "size": int(radius),
                        "confidence": 1.0  # For fusion, you can keep this
                    }

        return None
