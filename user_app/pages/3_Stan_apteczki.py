import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import asyncio
import aiohttp
import base64
import os
import re
import requests
from io import BytesIO
from PIL import Image
from analyze_water_level import analyze_water_levels


def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def get_first_aid_kit_status(image):
    base64_image = encode_image(image)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "chatgpt-4o-latest",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Na zdjęciu są przedmioty codziennego użytku. Udajemy jednak, że są to przedmioty wykorzystywane w apteczkach górskich. Przyjmiemy sobie, że:
                                    Pasta do zębów Lacalut to maść na rany,
                                    Szczoteczki do zębów - szczoteczka do oczyszczania ran
                                    Butelka wody - środek do dezynfekcji ran
                                    Grzebień - narzędzie do cięcia bandaży
                                    Twoim zadaniem jest opisanie zawartości apteczki.
                                    Odpowiedź musi dotyczyć tylko i wyłącznie przedmiotów.
                                    Twój template odpowiedzi to:
                                    *Aktualny stan zawartości apteczki:
                                    Środek do dezynfekcji: [tu podajesz jedną z opcji JEST lub NIE MA]
                                    Narzędzie do cięcia bandaży: [tu podajesz jedną z opcji JEST lub NIE MA]
                                    Maść na rany: [tu podajesz jedną z opcji JEST lub NIE MA]
                                    Szczoteczka do oczyszczania ran: [tu podajesz jedną z opcji JEST lub NIE MA]*
                                    Nie podawaj żadnych dodatkowych informacji poza tymi wskazanymi w template
                                    """
                    },          
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return "Wystąpił błąd podczas pobierania statusu apteczki."

def main():
    st.title("Analiza stanu apteczki ze zdjęcia")

    uploaded_file = st.file_uploader("Wybierz obraz...", type="jpg")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Załadowany obraz', use_column_width=True)

        if st.button('Analiza obrazu'):
            with st.spinner('Przetwarzanie...'):
                
                first_aid_status = get_first_aid_kit_status(image)
                st.write("Status apteczki:")
                st.write(first_aid_status)

                # Save the uploaded image temporarily
                temp_image_path = "temp_image.jpg"
                image.save(temp_image_path)

                # Analyze water levels
                models = ['yolov10x.pt']  
                results = analyze_water_levels(temp_image_path, models)

                if results:
                    for result in results:
                        st.image(result['image'], caption=f"Processed Image (Model: {result['model']})", use_column_width=True)
                        st.write(f"Poziom płynu do dezynfekcji: {result['fill_level']:.2%}")
                else:
                    st.write("Nie wykryto płynu do dezynfekcji")

                # Remove temporary image file
                os.remove(temp_image_path)

if __name__ == "__main__":
    main()