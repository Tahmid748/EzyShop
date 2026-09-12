"""FastAPI frontend and Telegram Web App onboarding endpoints."""

import hashlib
import hmac
import json
import shutil
from pathlib import Path
from urllib.parse import parse_qsl
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from telegram import Bot

from source.config.config import DEV_TELEGRAM_USER_ID, PUBLIC_BASE_URL, TELEGRAM_BOT_TOKEN
from source.database.store import (
    add_image, add_product, create_business, create_order, find_products, get_business, list_businesses,
)
from source.embeddings.clip import embed_image, embed_text

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "web_static"
UPLOADS = STATIC / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="EzyShop")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# CLIP cosine distance: lower means more visually similar. This is lenient
# enough for a product photo taken in a real-world setting, while rejecting
# clearly unrelated catalog items.
MAX_PRODUCT_MATCH_DISTANCE = 0.28


def telegram_user_id(init_data: str) -> int:
    """Verify Telegram Web App initData before trusting its user ID."""
    if not init_data and DEV_TELEGRAM_USER_ID:
        return int(DEV_TELEGRAM_USER_ID)
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", "")
    if not received_hash or not TELEGRAM_BOT_TOKEN:
        raise HTTPException(401, "Open this page from Telegram.")
    data_check = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(401, "Invalid Telegram Web App data.")
    try:
        return int(json.loads(values["user"])["id"])
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(401, "Missing Telegram user data.") from error


@app.get("/", response_class=HTMLResponse)
async def chat_page() -> FileResponse:
    return FileResponse(STATIC / "chat.html")


@app.get("/business/{slug}", response_class=HTMLResponse)
async def business_chat_page(slug: str) -> FileResponse:
    if not await get_business(slug):
        raise HTTPException(404, "Business not found.")
    return FileResponse(STATIC / "chat.html")


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page() -> FileResponse:
    return FileResponse(STATIC / "onboarding.html")


@app.get("/api/businesses")
async def businesses() -> list[dict]:
    return await list_businesses()


@app.post("/api/onboarding")
async def onboarding(
    init_data: str = Form(""),
    business_name: str = Form(...),
    items_json: str = Form(...),
    images: list[UploadFile] = File(...),
) -> dict:
    owner_id = telegram_user_id(init_data)
    if not business_name.strip() or not images:
        raise HTTPException(422, "Business name and at least one image are required.")
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as error:
        raise HTTPException(422, "Invalid inventory details.") from error
    if not isinstance(items, list) or len(items) != len(images):
        raise HTTPException(422, "Provide details for every uploaded image.")

    business = await create_business(owner_id, business_name.strip())
    created = 0
    for image, item in zip(images, items, strict=True):
        suffix = Path(image.filename or "image.jpg").suffix.lower() or ".jpg"
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(422, "Upload JPG, PNG, or WebP images only.")
        filename = f"{uuid4()}{suffix}"
        saved = UPLOADS / filename
        with saved.open("wb") as destination:
            shutil.copyfileobj(image.file, destination)
        product_id = await add_product(business["id"], {
            "name": str(item.get("name", "")).strip() or Path(image.filename or "Product").stem.replace("_", " ").title(),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 0)),
            "description": str(item.get("description", "")).strip() or "Product details to be confirmed by the seller.",
        })
        embedding = await embed_image(saved)
        await add_image(product_id, f"/static/uploads/{filename}", embedding)
        created += 1
    storefront_url = f"{PUBLIC_BASE_URL}/business/{business['slug']}"
    if TELEGRAM_BOT_TOKEN:
        async with Bot(TELEGRAM_BOT_TOKEN) as bot:
            await bot.send_message(owner_id, f"Your EzyShop storefront is ready: {storefront_url}")
    return {"ok": True, "business_id": business["id"], "storefront_url": storefront_url, "images_indexed": created}


@app.post("/api/chat")
async def customer_chat(message: str = Form(""), business_slug: str = Form(""), image: UploadFile | None = File(None)) -> dict:
    if image:
        saved = UPLOADS / f"search-{uuid4()}{Path(image.filename or '.jpg').suffix}"
        with saved.open("wb") as destination:
            shutil.copyfileobj(image.file, destination)
        vector = await embed_image(saved)
    elif message.strip():
        vector = await embed_text(message)
    else:
        raise HTTPException(422, "Write a message or attach an image.")
    products = await find_products(vector, limit=1, business_slug=business_slug or None)
    if products and float(products[0]["distance"]) > MAX_PRODUCT_MATCH_DISTANCE:
        products = []
    reply = "I found a matching product." if products else "I couldn't find a confident product match yet."
    return {"reply": reply, "products": products}


@app.get("/api/businesses/{slug}")
async def business(slug: str) -> dict:
    result = await get_business(slug)
    if not result:
        raise HTTPException(404, "Business not found.")
    return result


@app.post("/api/orders")
async def order(product_id: int = Form(...), name: str = Form(...), phone: str = Form(...), address: str = Form(...)) -> dict:
    result = await create_order(product_id, {"name": name, "phone": phone, "address": address})
    async with Bot(TELEGRAM_BOT_TOKEN) as bot:
        await bot.send_message(
            result["owner_id"],
            f"New order #{result['id']} for {result['product_name']}\n"
            f"Customer: {name}\nPhone: {phone}\nAddress: {address}",
        )
    return {"ok": True, "order_id": result["id"]}
