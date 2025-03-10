import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# DB_URI = os.getenv("DATABASE_URL") 

TOKEN = os.getenv("TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN") # WPP Token
WHATSAPP_URL = os.getenv("WHATSAPP_URL")

# BASE_URL = os.getenv("BASE_URL")

# GOOGLE_TOKEN = os.getenv("GOOGLE_TOKEN")

# UBICACION = os.getenv("UBICACION")
