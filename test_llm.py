from groq import Groq

from config import GROQ_API_KEY, MODEL_NAME
from prompts import SYSTEM_PROMPT


client = Groq(api_key=GROQ_API_KEY)


response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "RepoMedic brain connected"
            ),
        },
    ],
    temperature=0,
)


print(response.choices[0].message.content)