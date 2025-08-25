# """
# Configuration for environment variables and constants using openai api .
# """
# import os
# from dotenv import load_dotenv

# load_dotenv(override=True)
# os.environ["PYTHONWARNINGS"] = "ignore"

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")
# SUPABASE_HOST = os.getenv("SUPABASE_HOST")
# SUPABASE_PORT = os.getenv("SUPABASE_PORT")
# SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

# DB_URI = f"postgresql://postgres.{SUPABASE_PROJECT_REF}:{SUPABASE_DB_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/postgres"
# LLM_MODEL = "gemini-1.5-pro"
"""
Configuration for environment variables and constants using openrouter api .
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)
os.environ["PYTHONWARNINGS"] = "ignore"

SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")
SUPABASE_HOST = os.getenv("SUPABASE_HOST")
SUPABASE_PORT = os.getenv("SUPABASE_PORT")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

DEFAULT_DB_URI = f"postgresql://postgres.{SUPABASE_PROJECT_REF}:{SUPABASE_DB_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/postgres"

# DEFAULT_DB_URI = f"postgresql://postgres.gvtwqlrgymmjhfogupbc:KKD5Ii3DQEnFNnAq@aws-1-eu-west-3.pooler.supabase.com:5432/postgres" this s the sworking other database it needs to be ipv4 i already tried the connection it works so use it for testing 


DB_URI = DEFAULT_DB_URI
def set_db_uri(new_uri: str ):
    """Override DB_URI if given, else keep default."""
    global DB_URI
    DB_URI = new_uri 
    return DB_URI



# OpenRouter config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# OpenRouter base URL (fixed, no need to change)
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
# Model name (choose as needed)
LLM_MODEL = "moonshotai/kimi-k2:free"