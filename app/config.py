import os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env

R2_BUCKET_NAME = "loopi-media"
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./loopi.db")
