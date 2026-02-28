import cv2

stream = cv2.VideoCapture(0)

if not stream.isOpened():
    print("Error: No Video")
    exit()

while True:
    ret, frame = stream.read()

    if not ret:
        print("Error loading video")
        break
    frame = cv2.flip(frame, 1)
    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) == ord('q'):
        break

stream.release()
cv2.destroyAllWindows()
