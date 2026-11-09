import cv2
import mediapipe as mp
import os
import sys
import time
from datetime import datetime

FINGER_TIPS = [4, 8, 12, 16, 20]
COLORS = [
    (0, 0, 255),
    (0, 255, 0),
    (255, 0, 0),
    (0, 255, 255),
    (255, 0, 255),
]
PASSWORD = 8
STABLE = 15
state = "LOCKED"
action = "NONE"
unlock_count = 0
stable_gesture = "NONE"
stable_count = 0
countdown_start = 0
countdown_len = 0

if len(sys.argv) > 1 and sys.argv[1] != "--demo" and sys.argv[1].lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
    frame = cv2.imread(sys.argv[1])
    if frame is None:
        print(f"not found: {sys.argv[1]}")
        exit()
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    hands = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2)
    mp_drawing = mp.solutions.drawing_utils
    result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    total = 0
    gesture = "NONE"
    if result.multi_hand_landmarks:
        for point in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, point, mp.solutions.hands.HAND_CONNECTIONS)
            for i, tip in enumerate(FINGER_TIPS):
                px = int(point.landmark[tip].x * w)
                py = int(point.landmark[tip].y * h)
                cv2.circle(frame, (px, py), 12, COLORS[i], -1)
                cv2.circle(frame, (px, py), 12, (255, 255, 255), 2)
            lm = point.landmark
            states = [int(lm[4].y < lm[3].y)]
            for tip in [8, 12, 16, 20]:
                states.append(int(lm[tip].y < lm[tip - 2].y))
            total += sum(states)
            if states == [0, 1, 1, 0, 0]:
                gesture = "VICTORY"
            elif states == [1, 1, 1, 1, 1]:
                gesture = "OPEN_PALM"
            elif states == [1, 0, 0, 0, 0]:
                gesture = "THUMBS_UP"
    for _ in range(20):
        if state == "LOCKED":
            if total == PASSWORD:
                unlock_count += 1
                if unlock_count >= STABLE:
                    state = "UNLOCKED"
                    unlock_count = 0
            else:
                unlock_count = 0
        elif state == "UNLOCKED":
            if gesture == "NONE":
                stable_gesture = "NONE"
                stable_count = 0
            else:
                if gesture == stable_gesture:
                    stable_count += 1
                else:
                    stable_gesture = gesture
                    stable_count = 1
                if stable_count >= STABLE:
                    if gesture == "VICTORY":
                        action = "PHOTO"
                        state = "COUNTDOWN"
                    elif gesture == "THUMBS_UP":
                        action = "VIDEO"
                        state = "COUNTDOWN"
                    elif gesture == "OPEN_PALM":
                        state = "EXITED"
                    stable_gesture = "NONE"
                    stable_count = 0
    print(f"total={total} gesture={gesture} state={state} action={action}")
    cv2.putText(frame, state, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.imwrite("output.jpg", frame)
    print("output.jpg")
    hands.close()
elif len(sys.argv) > 1 and sys.argv[1] == "--demo":
    print("VICTORY" if [0, 1, 1, 0, 0] == [0, 1, 1, 0, 0] else "NONE")
    print("OPEN_PALM" if [1, 1, 1, 1, 1] == [1, 1, 1, 1, 1] else "NONE")
    print("THUMBS_UP" if [1, 0, 0, 0, 0] == [1, 0, 0, 0, 0] else "NONE")
    for _ in range(20):
        if state == "LOCKED":
            if 8 == PASSWORD:
                unlock_count += 1
                if unlock_count >= STABLE:
                    state = "UNLOCKED"
                    unlock_count = 0
    print(state)
    for _ in range(20):
        if "VICTORY" == stable_gesture:
            stable_count += 1
        else:
            stable_gesture = "VICTORY"
            stable_count = 1
        if stable_count >= STABLE:
            action = "PHOTO"
            state = "COUNTDOWN"
            stable_gesture = "NONE"
            stable_count = 0
    print(state, action)
else:
    cap = cv2.VideoCapture(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].lower().endswith((".mp4", ".avi", ".mov", ".mkv")) else 0)
    if not cap.isOpened():
        exit()
    hands = mp.solutions.hands.Hands(max_num_hands=2)
    mp_drawing = mp.solutions.drawing_utils
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        total = 0
        gesture = "NONE"
        if result.multi_hand_landmarks:
            for point in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, point, mp.solutions.hands.HAND_CONNECTIONS)
                for i, tip in enumerate(FINGER_TIPS):
                    px = int(point.landmark[tip].x * w)
                    py = int(point.landmark[tip].y * h)
                    cv2.circle(frame, (px, py), 12, COLORS[i], -1)
                    cv2.circle(frame, (px, py), 12, (255, 255, 255), 2)
                lm = point.landmark
                states = [int(lm[4].y < lm[3].y)]
                for tip in [8, 12, 16, 20]:
                    states.append(int(lm[tip].y < lm[tip - 2].y))
                total += sum(states)
                if states == [0, 1, 1, 0, 0]:
                    gesture = "VICTORY"
                elif states == [1, 1, 1, 1, 1]:
                    gesture = "OPEN_PALM"
                elif states == [1, 0, 0, 0, 0]:
                    gesture = "THUMBS_UP"
        if state == "COUNTDOWN":
            remaining = countdown_len - int(time.time() - countdown_start)
            if remaining <= 0:
                if action == "PHOTO":
                    os.makedirs("Photos", exist_ok=True)
                    path = f"Photos/img_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                    cv2.imwrite(path, frame)
                    print(path)
                    state = "UNLOCKED"
                    action = "NONE"
                elif action == "VIDEO":
                    os.makedirs("Videos", exist_ok=True)
                    path = f"Videos/video_{datetime.now():%Y%m%d_%H%M%S}.mp4"
                    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (640, 480))
                    start = time.time()
                    while time.time() - start < 5:
                        ret2, frame2 = cap.read()
                        if not ret2:
                            break
                        writer.write(cv2.resize(frame2, (640, 480)))
                        cv2.imshow("Hands", frame2)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
                    writer.release()
                    print(path)
                    state = "UNLOCKED"
                    action = "NONE"
            else:
                cv2.putText(frame, str(remaining), (w // 2 - 40, 200), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6)
        else:
            if state == "LOCKED":
                if total == PASSWORD:
                    unlock_count += 1
                    if unlock_count >= STABLE:
                        state = "UNLOCKED"
                        unlock_count = 0
                else:
                    unlock_count = 0
            elif state == "UNLOCKED":
                if gesture == "NONE":
                    stable_gesture = "NONE"
                    stable_count = 0
                else:
                    if gesture == stable_gesture:
                        stable_count += 1
                    else:
                        stable_gesture = gesture
                        stable_count = 1
                    if stable_count >= STABLE:
                        if gesture == "VICTORY":
                            action = "PHOTO"
                            state = "COUNTDOWN"
                        elif gesture == "THUMBS_UP":
                            action = "VIDEO"
                            state = "COUNTDOWN"
                        elif gesture == "OPEN_PALM":
                            state = "EXITED"
                        stable_gesture = "NONE"
                        stable_count = 0
            if state == "COUNTDOWN":
                countdown_len = 3 if action == "PHOTO" else 5
                countdown_start = time.time()
        cv2.putText(frame, state, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.imshow("Hands", frame)
        if state == "EXITED" or cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
