import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")


def call_llm(system_prompt: str, user_message: str) -> dict:
    full_system = (
        system_prompt
        + "\n\nIMPORTANT: Always respond with valid JSON only. No extra text, "
        "no markdown fences. Your entire response must be a single JSON object."
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_message}
        ]
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "parse_error": True}