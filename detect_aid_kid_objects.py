from ultralytics import YOLO
import cv2

def analyze_first_aid_kit(image_path):
    model = YOLO('moje_aid_yolov10m_v3.pt')

    results = model(image_path)

    detected_items = {
        'bottle': False,
        'toothbrush': False,
        'toothpaste': False,
        'hair brush': False
    }

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            class_name = model.names[cls]
            if class_name in detected_items:
                detected_items[class_name] = True

    output = "*Aktualny stan zawartości apteczki:\n"
    output += f"Środek do dezynfekcji: {'JEST' if detected_items['bottle'] else 'NIE MA'}\n"
    output += f"Narzędzie do cięcia bandaży: {'JEST' if detected_items['hair brush'] else 'NIE MA'}\n"
    output += f"Maść na rany: {'JEST' if detected_items['toothpaste'] else 'NIE MA'}\n"
    output += f"Szczoteczka do oczyszczania ran: {'JEST' if detected_items['toothbrush'] else 'NIE MA'}*"

    image = cv2.imread(image_path)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            class_name = model.names[cls]
            if class_name in detected_items:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                label_map = {
                    'bottle': 'Środek do dezynfekcji',
                    'hair brush': 'Narzędzie do cięcia bandaży',
                    'toothpaste': 'Maść na rany',
                    'toothbrush': 'Szczoteczka do oczyszczania ran'
                }
                label = label_map.get(class_name, class_name)
                
                cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imwrite('annotated_image.jpg', image)

    return output, 'annotated_image.jpg'