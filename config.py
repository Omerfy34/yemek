import os
from dotenv import load_dotenv

load_dotenv()

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Firebase
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")

# Flask
SECRET_KEY = "ne-pisirelim-gizli-anahtar-2025"

# Oylama ayarları
OYLAMA_KAPANIS_SAATI = 16
MENU_OLUSTURMA_SAATI = 0
GUNLUK_MENU_SAYISI = 3
GECMIS_GUN_SAYISI = 7
