import os

from dotenv import load_dotenv


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Available on the Groq developer API and supports local tool calling.
MODEL_NAME = "openai/gpt-oss-120b"

# Maximum number of tool/reasoning iterations.
MAX_AGENT_STEPS = 10


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. "
        "Add it to your .env file."
    )