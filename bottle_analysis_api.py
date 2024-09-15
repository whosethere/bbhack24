import cv2
import numpy as np
from ultralytics import YOLO
import asyncio
import aiohttp
import base64
import os
import re

# Stała zmienna na klucz API



def validate_api_key(api_key):
    if not api_key or not isinstance(api_key, str) or len(api_key) < 20:
        raise ValueError("Nieprawidłowy klucz API")
    return api_key.strip()  # Usuwa ewentualne białe znaki


# async def analyze_bottle_fill_level(image_bytes):
#     # Zapisz tymczasowo obraz
#     temp_image_path = 'temp_image.jpg'
#     with open(temp_image_path, 'wb') as f:
#         f.write(image_bytes)

#     # Wczytaj model YOLO
#     model = YOLO('yolov10x.pt')

#     # Wczytaj obraz
#     image = cv2.imread(temp_image_path)
#     if image is None:
#         print("Nie udało się wczytać obrazu")
#         os.remove(temp_image_path)
#         return None

#     # Wykonaj detekcję YOLO
#     results = model(image)

#     bottles = []
#     for r in results:
#         boxes = r.boxes
#         for box in boxes:
#             cls = int(box.cls[0])
#             if model.names[cls] == 'bottle':
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 bottles.append((x1, y1, x2, y2))

#     # Jeśli znaleziono butelki, wyślij zdjęcie do API
#     if bottles:
#         try:
#             fill_level = await get_fill_level_from_api(temp_image_path)
#         except Exception as e:
#             print(f"Błąd podczas komunikacji z API: {str(e)}")
#             fill_level = None
#     else:
#         print("Nie wykryto żadnej butelki na zdjęciu.")
#         fill_level = None

#     # Usuń tymczasowy plik
#     os.remove(temp_image_path)

#     return fill_level

# async def get_fill_level_from_api(image_path):
#     try:
#         api_key = validate_api_key(OPENAI_API_KEY)
#     except ValueError as e:
#         print(f"Błąd walidacji klucza API: {str(e)}")
#         return None

#     base64_image = encode_image(image_path)

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_key}"
#     }

#     payload = {
#         "model": "gpt-4o-2024-08-06",  # Zmieniono model na zgodny z aktualną ofertą OpenAI
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "text",
#                         "text": "Twoim zadaniem jest odpowiedzieć na pytanie jak bardzo wypełniona jest butelka wodą. W odpowiedzi zwrotnie podaj % napełnienia butelki. Pamiętaj, że butelka wody w sklepie kiedy jest nieotwarta - nie jest napełniona po sam czubek. Tylko i wyłącznie. Jeśli na zdjęciu nie widzisz butelki, zwróć odpowiedź \"None\". W odpowiedzi zwrotnie przekaż tylko i wyłącznie procent napełnienia butelki, bez przedziału procentowego 50\%-70\%, tylko i wyłącznie ostateczny stan."
#                     },
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:image/jpeg;base64,{base64_image}"
#                         }
#                     },
#                 ]
#             }
#         ],
# #         "max_tokens": 300
# #     }

# #     print(f"Używany klucz API: {api_key[:5]}...{api_key[-5:]}")  # Pokazuje tylko początek i koniec klucza

#     async with aiohttp.ClientSession() as session:
#         async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
#             if response.status == 200:
#                 data = await response.json()
#                 content = data['choices'][0]['message']['content']
#                 print(f"API response: {content}")
#                 if content.lower() == 'none':
#                     return None
#                 numbers = re.findall(r'\d+', content)
#                 if numbers:
#                     return float(numbers[0]) / 100
#                 else:
#                     print(f"Nie znaleziono liczby w odpowiedzi: {content}")
#                     return None
#             else:
#                 error_detail = await response.text()
#                 print(f"API request failed with status code: {response.status}")
#                 print(f"Error details: {error_detail}")
#                 print(f"Użyte nagłówki: {headers}")
#                 return None

# Funkcja pomocnicza do kodowania obrazu
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')