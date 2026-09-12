import base64
import json

from openai import AsyncOpenAI

from source.config.config import OPENROUTER_API_KEY

client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


async def generate_details(image_bytes: bytes, mime_type: str) -> dict[str, object]:
    """Create an editable product-listing draft by analysing a product photo."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    response = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You create accurate, concise ecommerce listing drafts from a product photo. "
                    "Return JSON only, with exactly: name (string), description (string), "
                    "price (number; a clearly labelled estimate in USD), quantity (integer; default 1). "
                    "Never invent precise technical specifications that cannot be seen."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Generate an editable listing draft for this inventory item."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )
    details = json.loads(response.choices[0].message.content or "{}")
    return {
        "name": str(details.get("name", "")),
        "description": str(details.get("description", "")),
        "price": max(0, float(details.get("price", 0))),
        "quantity": max(0, int(details.get("quantity", 1))),
    }
