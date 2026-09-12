First -
First of all,
initiate the database by running the database.py function once
configure telegram

## Registration lookup

Set `DATABASE_URL` in `.env`, then run `python initiate_database.py` once.
The bot checks `registered_users.telegram_user_id` before every response and
passes the result to `generate_response(..., is_registered=<bool>)`.

To mark a Telegram user as registered, insert their numeric Telegram user ID:

```sql
INSERT INTO registered_users (telegram_user_id) VALUES (123456789);
```

## Web app and inventory search

Install the updated dependencies, then run `python initiate_database.py` again
to add the business, product, order and pgvector tables. Start everything with
`python main.py`; the customer chat is available at `http://localhost:8000`.

Set `TELEGRAM_WEB_APP_URL` to your public ngrok address plus `/onboarding`,
then restart the bot. The bot gives registered sellers a Telegram Web App
button. Sellers enter their business name and batch-upload product images.
Images are stored locally in `web_static/uploads` and embedded by the local
CLIP model (`openai/clip-vit-base-patch32`), not by an embedding API.

Set `PUBLIC_BASE_URL` to the same ngrok address without `/onboarding`. After
onboarding, the bot sends the seller a permanent storefront URL in the form
`/business/<business-slug>`. Customer searches on that page are restricted to
that business's inventory.

For a local browser-only onboarding test, set `DEV_TELEGRAM_USER_ID` to the
numeric ID of a registered Telegram user. Keep it empty in production because
Telegram Web App `initData` is then cryptographically verified.
