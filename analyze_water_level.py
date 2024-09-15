from ultralytics import YOLO
import cv2
import numpy as np

def detect_water_level(bottle_region):
    gray = cv2.cvtColor(bottle_region, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    hist = cv2.calcHist([blurred], [0], None, [256], [0, 256])
    peaks = np.argsort(hist.flatten())[-2:]
    threshold = np.mean(peaks)
    _, thresholded = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        highest_point = tuple(largest_contour[largest_contour[:, :, 1].argmin()][0])
        return highest_point[1]
    
    return None

def analyze_water_levels(image_path, models):
    results = []
    
    for model_name in models:
        try:
            model = YOLO(model_name)
            image = cv2.imread(image_path)
            
            model_results = model(image)
            for r in model_results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    if model.names[cls] == 'bottle':
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bottle_region = image[y1:y2, x1:x2]
                        water_level = detect_water_level(bottle_region)
                        
                        if water_level is not None:
                            bottle_height = y2 - y1
                            fill_level = 1 - (water_level / bottle_height)
                            
                            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
                            fill_y = y1 + water_level
                            cv2.line(image, (x1, fill_y), (x2, fill_y), (0, 0, 255), 2)
                            cv2.putText(image, f'Buteleczka: {fill_level:.2%}', (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                            
                            results.append({
                                'model': model_name,
                                'fill_level': fill_level,
                                'image': image
                            })
            
            cv2.putText(image, f'Model: {model_name}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            output_path = f'wynik_{model_name.replace(".pt", "")}.jpg'
            cv2.imwrite(output_path, image)
            print(f"Analiza zakończona dla modelu {model_name}. Wynik zapisano jako '{output_path}'")
        
        except Exception as e:
            print(f"Wystąpił błąd podczas przetwarzania modelu {model_name}: {str(e)}")
    
    return results
