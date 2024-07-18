import cv2
import requests
import numpy as np
from ultralytics import YOLO
import io
import json
import socket

# URL set
stream_url = "http://192.168.43.85:8000/stream"

# port
host = '192.168.43.143'
port = 12001

# Load model
model = YOLO("yolov8s.pt")

resize_width = 320
resize_height = 240

# Dictionary to keep track of object tags
object_tags = {}
next_tag = 1

def assign_tag(bbox):
    global next_tag
    for tag, previous_bbox in object_tags.items():
        if iou(bbox, previous_bbox) > 0.5:
            object_tags[tag] = bbox  # position updating
            return tag
    object_tags[next_tag] = bbox
    next_tag += 1
    return next_tag - 1

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)

def fetch_frames(bytes_buffer, num_frames=3):
    frames = []
    while len(frames) < num_frames:
        if b'\xff\xd8' in bytes_buffer and b'\xff\xd9' in bytes_buffer:
            start = bytes_buffer.find(b'\xff\xd8')
            end = bytes_buffer.find(b'\xff\xd9', start) + 2
            jpg = bytes_buffer[start:end]
            bytes_buffer = bytes_buffer[end:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                frames.append(frame)
        else:
            break
    return frames, bytes_buffer

def process_frame(frame):
    resized_frame = cv2.resize(frame, (resize_width, resize_height))
    rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
    results = model(rgb_frame)
    result = results[0]

    bboxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    classes = result.boxes.cls.cpu().numpy()
    class_labels = [model.names[int(cls)] for cls in classes]

    scale_x = frame.shape[1] / resize_width
    scale_y = frame.shape[0] / resize_height
    bboxes[:, [0, 2]] *= scale_x
    bboxes[:, [1, 3]] *= scale_y

    detections = []

    for bbox, label, score in zip(bboxes, class_labels, scores):
        x1, y1, x2, y2 = bbox
        tag = assign_tag(bbox)
        detections.append({
            "label": label,
            "score": float(score),
            "tag": tag,
            "bbox": [int(x1), int(y1), int(x2), int(y2)]
        })
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        cv2.putText(frame, f"{label} {score:.2f} Tag:{tag}", (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # JSON comp.
    json_data = json.dumps(detections, indent=4)
    print(json_data)

    send_data(json_data)

    return frame

def send_data(data):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.send(data.encode())
    except Exception as e:
        print(f"Error sending data: {e}")
    finally:
        client_socket.close()

def fetch_and_process_stream(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        bytes_buffer = b''
        for chunk in r.iter_content(chunk_size=4096):
            bytes_buffer += chunk
            frames, bytes_buffer = fetch_frames(bytes_buffer)

            for frame in frames:
                processed_frame = process_frame(frame)
                cv2.imshow('Object Detection', processed_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return

        cv2.destroyAllWindows()
    else:
        print("Failed to connect to the stream.")

if __name__ == "__main__":
    fetch_and_process_stream(stream_url)
