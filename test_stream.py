import cv2

STREAM_URL = "rtsps://192.168.0.1:7441/0Fbr6A8qimkATMiy?enableSrtp"

print("Attempting to connect to stream...")
cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("Failed to open stream")
else:
    print("Stream opened successfully")
    ret, frame = cap.read()
    if ret:
        print(f"Frame captured: {frame.shape}")
        cv2.imwrite("test_frame.jpg", frame)
        print("Saved to test_frame.jpg")
    else:
        print("Stream opened but couldn't read frame")
    cap.release()
