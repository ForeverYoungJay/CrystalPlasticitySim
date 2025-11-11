import os

# Load from env (or use python-dotenv if you prefer)
LANGSMITH_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGSMITH_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY")             # set in env, not code
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "damask_agent")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")                   # set in env
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

def apply_env():
    os.environ["LANGCHAIN_TRACING_V2"] = LANGSMITH_TRACING
    os.environ["LANGCHAIN_ENDPOINT"]  = LANGSMITH_ENDPOINT
    if LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"]   = LANGSMITH_PROJECT
