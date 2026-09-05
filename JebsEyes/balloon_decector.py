# Key is "NJizlgFRD2r8gIg62y8E"

import cv2
import os
import tempfile

from inference_sdk import (
    InferenceHTTPClient,
    InferenceConfiguration
)


# ============================================================
# ROBOFLOW CONFIGURATION
# ============================================================

ROBOFLOW_API_KEY = "NJizlgFRD2r8gIg62y8E"

WORKSPACE_NAME = "jagman05"
WORKFLOW_ID = "balloon-color-detection-v8vdm"


# ============================================================
# ROBOFLOW CLIENT
# ============================================================

client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=ROBOFLOW_API_KEY
).configure(
    InferenceConfiguration(
        api_key_transport="header"
    )
)


# ============================================================
# BALLOON DETECTOR
# ============================================================

class BalloonDetector:

    def __init__(self):
        print("Initializing Roboflow balloon detector...")
        self.client = client
        print("✓ Roboflow balloon detector ready.")

    # --------------------------------------------------------
    # DETECT
    # --------------------------------------------------------

    def detect(self, frame):
        """
        Send an OpenCV frame to Roboflow.

        Returns:
            list of detections

        Each detection looks like:

        {
            "class": "black_balloon",
            "confidence": 0.91,
            "x": 632,
            "y": 347,
            "width": 214,
            "height": 281
        }
        """

        temp_path = None

        try:

            # ------------------------------------------------
            # Create temporary JPEG
            # ------------------------------------------------

            with tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name

            # ------------------------------------------------
            # Save OpenCV frame
            # ------------------------------------------------

            success = cv2.imwrite(
                temp_path,
                frame
            )

            if not success:
                print("⚠ Could not save temporary image.")
                return []

            # ------------------------------------------------
            # Run Roboflow workflow
            # ------------------------------------------------

            result = self.client.run_workflow(
                workspace_name=WORKSPACE_NAME,
                workflow_id=WORKFLOW_ID,

                images={
                    "image": temp_path
                },

                parameters={
                    "confidence": 0.4,
                    "iou_threshold": 0.3,
                    "class_agnostic_nms": False,
                    "max_detections": 1000
                },

                use_cache=False
            )

            # ------------------------------------------------
            # Parse Roboflow response
            # ------------------------------------------------

            return self._parse_result(result)

        except Exception as e:

            print(
                f"⚠ Roboflow inference error: {e}"
            )

            return []

        finally:

            # ------------------------------------------------
            # Delete temporary image
            # ------------------------------------------------

            if temp_path is not None:

                try:
                    os.remove(temp_path)

                except Exception:
                    pass

    # --------------------------------------------------------
    # PARSE RESULT
    # --------------------------------------------------------

    def _parse_result(self, result):
        """
        Convert the nested Roboflow response into a simple
        list of balloon detections.
        """

        detections = []

        if not result:
            return detections

        try:

            # Roboflow workflow returns a list
            workflow_result = result[0]

            predictions = workflow_result.get(
                "predictions",
                {}
            )

            predictions = predictions.get(
                "predictions",
                []
            )

            for prediction in predictions:

                detection = {
                    "class": prediction.get("class"),
                    "confidence": float(
                        prediction.get("confidence", 0)
                    ),
                    "x": float(
                        prediction.get("x", 0)
                    ),
                    "y": float(
                        prediction.get("y", 0)
                    ),
                    "width": float(
                        prediction.get("width", 0)
                    ),
                    "height": float(
                        prediction.get("height", 0)
                    )
                }

                detections.append(detection)

        except Exception as e:

            print(
                f"⚠ Could not parse Roboflow result: {e}"
            )

        return detections

    # --------------------------------------------------------
    # GET BEST BALLOON
    # --------------------------------------------------------

    def get_best_balloon(
        self,
        detections,
        target_class
    ):
        """
        Find the highest-confidence balloon matching
        the requested target class.

        Example:

            target_class = "black_balloon"

        Returns the best matching detection,
        or None if the target isn't detected.
        """

        matching = [
            detection
            for detection in detections
            if detection["class"] == target_class
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda detection: detection["confidence"]
        )
# ```

# ### What changed?

# Your Roboflow request itself is basically **unchanged**.

# We've added:

# ```text
# Roboflow response
#        ↓
# _parse_result()
#        ↓
# clean list
# ```

# So instead of Jeb having to deal with this:

# ```text
# [{
#     "predictions": {
#         "image": {...},
#         "predictions": [...]
#     }
# }]
# ```

# it gets:

# ```text
# [
#     {
#         "class": "black_balloon",
#         "confidence": 0.91,
#         "x": 632,
#         "y": 347,
#         "width": 214,
#         "height": 281
#     }
# ]
# ```

# And then we can simply ask:

# ```python
# black = detector.get_best_balloon(
#     detections,
#     "black_balloon"
# )
# ```

# If black is visible:

# ```text
# black = {
#     class: black_balloon,
#     confidence: 0.91,
#     x: 632,
#     y: 347,
#     ...
# }
# ```

# If it isn't:

# ```text
# black = None
# ```

# ---

# ## Then we'll add the mission controller

# The next piece will be something like:

# ```python
# MISSION = [
#     "black_balloon",
#     "white_balloon",
#     "pink_balloon",
#     "yellow_balloon",
#     "blue_balloon"
# ]
# ```

# with:

# ```text
# current_target = black_balloon

#         ↓

# Is black detected?

#    NO → keep searching

#    YES
#     ↓
# TARGET ACQUIRED
#     ↓
# [future: approach]
#     ↓
# [future: ≤1.5 m]
#     ↓
# [future: STOP 5 seconds]
#     ↓
# current_target = white_balloon
# ```

# **For now, don't connect this to the Pico.** Let's first verify that the parser works with your actual Roboflow output. Once you've replaced the file, run Jeb again and send me the output. Then we'll hook this into `main.py` and build the mission state machine.
