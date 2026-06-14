from dotenv import load_dotenv
import os

load_dotenv()

AZURE_AIPROJECT_ENDPOINT = os.environ["AZURE_AIPROJECT_ENDPOINT"]
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")
APP_ENV = os.getenv("APP_ENV", "development")
