"""Create the table used to determine whether a Telegram user is registered.

Run once after setting DATABASE_URL in .env:
    python initiate_database.py
"""

from psycopg import connect

from source.config.config import DATABASE_URL


def initialise_database() -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set in .env before initializing the database")

    with connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE EXTENSION IF NOT EXISTS vector;

                CREATE TABLE IF NOT EXISTS registered_users (
                    telegram_user_id BIGINT PRIMARY KEY,
                    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS businesses (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL UNIQUE REFERENCES registered_users(telegram_user_id),
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                ALTER TABLE businesses ADD COLUMN IF NOT EXISTS slug TEXT;
                UPDATE businesses SET slug = 'shop-' || telegram_user_id WHERE slug IS NULL;
                ALTER TABLE businesses ALTER COLUMN slug SET NOT NULL;
                CREATE UNIQUE INDEX IF NOT EXISTS businesses_slug_idx ON businesses(slug);

                CREATE TABLE IF NOT EXISTS products (
                    id BIGSERIAL PRIMARY KEY,
                    business_id BIGINT NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
                    quantity INTEGER NOT NULL CHECK (quantity >= 0),
                    description TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS product_images (
                    id BIGSERIAL PRIMARY KEY,
                    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    image_path TEXT NOT NULL,
                    embedding vector(512) NOT NULL
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id BIGSERIAL PRIMARY KEY,
                    product_id BIGINT NOT NULL REFERENCES products(id),
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    customer_address TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS product_images_embedding_idx
                    ON product_images USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
                """
            )
        connection.commit()


if __name__ == "__main__":
    initialise_database()
    print("EzyShop database schema is ready")
