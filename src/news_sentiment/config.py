import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
    FINBERT_MODEL = "ProsusAI/finbert"
