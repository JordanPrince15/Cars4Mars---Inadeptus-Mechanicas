import cv2
import numpy as np

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

LOWER_GREEN = np.array([25, 80, 80])
UPPER_GREEN = np.array([40, 255, 255])

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create mask
    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

    # Clean up noise
    mask = cv2.GaussianBlur(mask, (11, 11), 0)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:
        # Largest green object
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 500:  # ignore tiny noise
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if radius > 10:
                # Draw circle
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)

                # Position estimation
                frame_width = frame.shape[1]
                if x < frame_width / 3:
                    position = "LEFT"
                elif x > 2 * frame_width / 3:
                    position = "RIGHT"
                else:
                    position = "CENTER"

                cv2.putText(
                    frame,
                    f"Tennis Ball - {position}",
                    (int(x) - 60, int(y) - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

                print(f"Tennis Ball at {position}")

    cv2.imshow("Tennis Ball Tracking", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('d'):
        break

cap.release()
cv2.destroyAllWindows()
