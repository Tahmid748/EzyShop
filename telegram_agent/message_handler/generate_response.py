import json
from dataclasses import dataclass

from openai import AsyncOpenAI
from source.config.config import OPENROUTER_API_KEY

# OpenRouter is OpenAI-compatible; HTTPS here is just OpenRouter's remote endpoint
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """You are EzyShop's business setup assistant. Help a Telegram business
owner create their shop. You know whether they are registered from the supplied
context. Never ask users to type commands. If an unregistered user clearly agrees
to register, choose REGISTER_USER. Once registered, guide them to add a business
name and inventory through the onboarding page, using OPEN_ONBOARDING when ready.

Your entire response MUST be valid JSON with exactly these keys:
{"reply": "short, friendly text for the user", "action": null | "REGISTER_USER" | "OPEN_ONBOARDING"}
Do not wrap the JSON in Markdown or add any other text."""


@dataclass
class AgentResponse:
    reply: str
    action: str | None = None

async def generate_response(
    prompt: str,
    is_registered: bool,
    model: str = "openai/gpt-4o-mini"
) -> AgentResponse:
    print("generating response...")
    
    messages = []
    if SYSTEM_PROMPT:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})

    # Keep the registration state explicit for prompt logic that needs to
    # offer different flows to registered and unregistered users.
    messages.append(
        {
            "role": "system",
            "content": f"The current user is registered: {is_registered}.",
        }
    )
    
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )
    
    print("response generated")

    content = response.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        action = parsed.get("action")
        if action not in {None, "REGISTER_USER", "OPEN_ONBOARDING"}:
            action = None
        return AgentResponse(reply=str(parsed.get("reply", "")), action=action)
    except (json.JSONDecodeError, TypeError):
        # A safe fallback lets the conversation continue if the model misses
        # the required response shape.
        return AgentResponse(reply=content)
