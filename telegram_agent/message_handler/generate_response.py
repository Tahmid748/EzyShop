from openai import AsyncOpenAI
from source.config.config import OPENROUTER_API_KEY

# OpenRouter is OpenAI-compatible; HTTPS here is just OpenRouter's remote endpoint
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = "you are a helpful agent"

async def generate_response(
    prompt: str,
    model: str = "openai/gpt-4o-mini"
) -> str:
    print("generating response...")
    
    messages = []
    if SYSTEM_PROMPT:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )
    
    print("response generated")

    return response.choices[0].message.content or ""