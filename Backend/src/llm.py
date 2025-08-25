from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Pick whichever is available
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
model = os.getenv("LLM_MODEL") or "gpt-4o-mini"

if not api_key:
    raise ValueError("No API key found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY in .env")

llm = ChatOpenAI(
    model_name=model,
    openai_api_key=api_key.strip(),   # strip whitespace just in case
    openai_api_base=api_base,
    temperature=0,  # Set temperature to 0 for deterministic responses

)
