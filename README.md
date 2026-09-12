# EzyShop

EzyShop lets a Telegram seller create an image-searchable inventory and share a storefront chat with customers. Customers can search products by photo or natural language, receive a recommendation, and submit an order to the seller.

## Features

- AI-guided registration and business onboarding through Telegram.
- Telegram Web App for business name, batch image upload, and per-item editing.
- AI image analysis generates editable listing drafts: name, description, estimated price, and quantity.
- Local CLIP embeddings stored in PostgreSQL with pgvector—no embedding API.
- A permanent public storefront for every business: `/business/<slug>`.
- Image search returns only the top confident product match.
- Catalog-aware shopping agent reads product names and descriptions for text recommendations.
- Buy form collects customer name, phone, and address and notifies the seller in Telegram.

## Architecture

```text
Telegram seller → registration assistant → Telegram Web App (/onboarding)
                                      └→ AI listing drafts + local CLIP vectors
                                                        ↓
Customer storefront (/business/<slug>) → image search or catalog AI agent
                                                        ↓
                                        Buy form → seller Telegram notification
```

`main.py` starts both the Telegram polling bot and FastAPI web server. Uvicorn listens on local port `8000`; ngrok makes it publicly reachable.

## Prerequisites

- Python 3.11+
- PostgreSQL with pgvector available
- Telegram bot token from BotFather
- OpenRouter API key (for the seller assistant, vision listing drafts, and customer text agent)
- ngrok HTTPS tunnel forwarding to port `8000`

Install dependencies:

```powershell
pip install -r requirements.txt
```

The local embedding model is `openai/clip-vit-base-patch32`. It is cached locally after its first download and is used only for vector search.

## Configuration

Create a project `.env` file with real values. Do not commit it.

```env
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
OPENROUTER_API_KEY="your-openrouter-api-key"
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5431/postgres"

PUBLIC_BASE_URL="https://your-subdomain.ngrok-free.app"
TELEGRAM_WEB_APP_URL="https://your-subdomain.ngrok-free.app/onboarding"

WEB_HOST="0.0.0.0"
WEB_PORT="8000"

# For local browser-only Web App testing. Leave blank in production.
DEV_TELEGRAM_USER_ID=""
```

`0.0.0.0:8000` is the local server bind address, not a public URL. Use the ngrok HTTPS address for Telegram buttons and storefront links. If ngrok gives you a new free URL, update both public URL settings and restart the app.

## Database setup

After configuring `DATABASE_URL`, initialize or update the schema:

```powershell
python initiate_database.py
```

It is safe to run this command again. It enables pgvector and creates these tables:

| Table | Purpose |
| --- | --- |
| `registered_users` | Telegram seller registration status |
| `businesses` | Seller business and public slug |
| `products` | Names, descriptions, prices, and stock |
| `product_images` | Image paths and 512-dimensional vector embeddings |
| `orders` | Customer order/contact information |

## Start EzyShop

Start ngrok in one terminal:

```powershell
ngrok http 8000
```

Copy its HTTPS forwarding URL into `PUBLIC_BASE_URL` and `TELEGRAM_WEB_APP_URL`, then start the application:

```powershell
python main.py
```

Expected output:

```text
Uvicorn running on http://0.0.0.0:8000
Bot and web app are running on http://0.0.0.0:8000
```

## Seller flow

1. A seller chats with the bot and agrees to register.
2. The AI emits a structured `REGISTER_USER` action; the server handles it, not the seller.
3. The bot sends a **Set up my business** Web App button.
4. The seller enters a business name and selects inventory images.
5. A separate form appears for every image, with the source image visible.
6. **Generate details with AI** analyses that image and fills an editable listing draft.
7. On **Save & index inventory**, a loading screen appears while product records and local CLIP vectors are saved.
8. The completion screen offers a storefront link and Close button; the bot also sends the seller their public URL.

## Customer flow

Each seller receives a URL such as:

```text
https://your-subdomain.ngrok-free.app/business/acme-fashion-123456789
```

Customers can:

- Choose an image. A thumbnail is shown in the message composer before sending. The server embeds it locally with CLIP and finds the top confident pgvector match.
- Ask questions such as “Do you have a black graphics card?” The shopping agent checks only that business’s real product names and descriptions, recommends a matching item, or explains that none match.
- Say they want to buy/order an item. When the agent finds a real catalog item, it opens the Buy form.
- Enter name, phone, and delivery address. The seller receives the order on Telegram. Payment processing is intentionally not included.

## Important files

| File | Responsibility |
| --- | --- |
| `main.py` | Starts bot polling and FastAPI |
| `web_app.py` | Web App, storefront, search, agent, and order endpoints |
| `telegram_agent/message_handler/generate_response.py` | Seller assistant structured responses |
| `source/commands/handle_commands.py` | Safe server-side AI action handling |
| `source/embeddings/clip.py` | Local CLIP image/text embeddings |
| `source/inventory/generate_details.py` | Vision-generated listing details |
| `source/agent/customer_agent.py` | Catalog-aware customer shopping agent |
| `initiate_database.py` | PostgreSQL/pgvector schema initializer |

## Troubleshooting

### `Conflict: terminated by other getUpdates request`

More than one process is polling the same bot token. Stop all old bot instances and run only one `python main.py` process.

### Telegram Web App does not open

Telegram requires public HTTPS. Verify ngrok is running and `TELEGRAM_WEB_APP_URL` ends in `/onboarding`.

### `Psycopg cannot use the ProactorEventLoop`

This project uses synchronous psycopg calls in `asyncio.to_thread`, which works on Windows. Restart with the current project code.

### `relation ... does not exist`

Run `python initiate_database.py` against the database configured in `.env`.

### Product search is inaccurate

Use a clear, tightly framed product image. EzyShop returns the single closest result only when it meets its confidence threshold. Re-uploading clear catalog photos improves matching.

### Frontend changes do not appear

Hard-refresh (`Ctrl+F5`) or reopen the Telegram Web App. Restart `python main.py` after Python backend changes.

## Security and production notes

- Telegram Web App identity is verified with Telegram `initData`; leave `DEV_TELEGRAM_USER_ID` empty in production.
- Generated listing details, especially price and quantity, are drafts and must be reviewed by the seller.
- Uploaded images live in `web_static/uploads`; move them to persistent protected object storage for production.
- Customer contact data is stored in PostgreSQL. Secure the database and follow applicable privacy requirements.
