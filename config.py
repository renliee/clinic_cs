import os
from dotenv import load_dotenv

load_dotenv() #read .env file

LLM_MODEL = os.getenv("LLM_MODEL")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")