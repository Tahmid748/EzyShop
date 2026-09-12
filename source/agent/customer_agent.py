import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from source.config.config import OPENROUTER_API_KEY

client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


@dataclass
class CustomerAgentResponse:
    reply: str
    product_id: int | None
    open_buy: bool


async def answer_customer(message: str, catalog: list[dict[str, Any]]) -> CustomerAgentResponse:
    """Recommend only a real catalog item, based on its stored description."""
    if not OPENROUTER_API_KEY:
        return CustomerAgentResponse("The shopping assistant is not configured right now.", None, False)
    catalog_text = json.dumps(catalog, ensure_ascii=False)
    response = await client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful shopping assistant. Use only the supplied catalog; never invent a product, "
                    "price, availability, or specification. Match requests using product names and descriptions. "
                    "If no item clearly matches, say so and leave product_id null. If the user explicitly says they "
                    "want to buy/order/purchase an item, set open_buy true only for the selected product. "
                    "Return JSON only: {reply: string, product_id: integer|null, open_buy: boolean}.\n"
                    f"CATALOG: {catalog_text}"
                ),
            },
            {"role": "user", "content": message},
        ],
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response.choices[0].message.content or "{}")
    valid_ids = {product["id"] for product in catalog}
    product_id = parsed.get("product_id")
    product_id = product_id if isinstance(product_id, int) and product_id in valid_ids else None
    return CustomerAgentResponse(
        reply=str(parsed.get("reply", "I couldn't find a matching product.")),
        product_id=product_id,
        open_buy=bool(parsed.get("open_buy")) and product_id is not None,
    )
