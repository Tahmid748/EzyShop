"""Synchronous PostgreSQL operations exposed as async-safe helpers."""

import asyncio
import logging
import re
from typing import Any

from psycopg import connect

from source.config.config import DATABASE_URL

logger = logging.getLogger(__name__)


def _require_database() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return DATABASE_URL


def _register_user(telegram_user_id: int) -> None:
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO registered_users (telegram_user_id) VALUES (%s) "
            "ON CONFLICT (telegram_user_id) DO NOTHING",
            (telegram_user_id,),
        )


async def register_user(telegram_user_id: int) -> None:
    await asyncio.to_thread(_register_user, telegram_user_id)


def _slugify(name: str, telegram_user_id: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "shop"
    return f"{base[:48]}-{telegram_user_id}"


def _create_business(telegram_user_id: int, name: str) -> dict[str, Any]:
    slug = _slugify(name, telegram_user_id)
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO businesses (telegram_user_id, name, slug) VALUES (%s, %s, %s) "
            "ON CONFLICT (telegram_user_id) DO UPDATE SET name = EXCLUDED.name "
            "RETURNING id, slug",
            (telegram_user_id, name, slug),
        )
        row = cursor.fetchone()
        return {"id": row[0], "slug": row[1]}


async def create_business(telegram_user_id: int, name: str) -> dict[str, Any]:
    return await asyncio.to_thread(_create_business, telegram_user_id, name)


def _add_product(business_id: int, product: dict[str, Any]) -> int:
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO products (business_id, name, price, quantity, description)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (business_id, product["name"], product["price"], product["quantity"], product["description"]),
        )
        return cursor.fetchone()[0]


async def add_product(business_id: int, product: dict[str, Any]) -> int:
    return await asyncio.to_thread(_add_product, business_id, product)


def _add_image(product_id: int, image_path: str, embedding: list[float]) -> None:
    vector = "[" + ",".join(str(value) for value in embedding) + "]"
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO product_images (product_id, image_path, embedding) VALUES (%s, %s, %s::vector)",
            (product_id, image_path, vector),
        )


async def add_image(product_id: int, image_path: str, embedding: list[float]) -> None:
    await asyncio.to_thread(_add_image, product_id, image_path, embedding)


def _find_products(embedding: list[float], limit: int, business_slug: str | None = None) -> list[dict[str, Any]]:
    vector = "[" + ",".join(str(value) for value in embedding) + "]"
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        # DISTINCT ON selects the closest uploaded photo per product.  The
        # outer query then orders products by that distance, rather than by
        # product ID (which would make unrelated early products appear first).
        query = """WITH nearest_product_images AS (
                       SELECT DISTINCT ON (p.id)
                              p.id, p.name, p.price, p.quantity, p.description,
                              b.name AS business_name, pi.image_path,
                              (pi.embedding <=> %s::vector) AS distance
                       FROM product_images pi
                       JOIN products p ON p.id = pi.product_id
                       JOIN businesses b ON b.id = p.business_id"""
        if business_slug:
            query += " WHERE b.slug = %s"
            parameters = (vector, business_slug, limit)
        else:
            parameters = (vector, limit)
        query += " ORDER BY p.id, distance) SELECT * FROM nearest_product_images ORDER BY distance LIMIT %s"
        cursor.execute(query, parameters)
        columns = [column.name for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


async def find_products(embedding: list[float], limit: int = 3, business_slug: str | None = None) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_find_products, embedding, limit, business_slug)


def _create_order(product_id: int, customer: dict[str, str]) -> dict[str, Any]:
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO orders (product_id, customer_name, customer_phone, customer_address)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (product_id, customer["name"], customer["phone"], customer["address"]),
        )
        order_id = cursor.fetchone()[0]
        cursor.execute(
            """SELECT b.telegram_user_id, p.name FROM products p
               JOIN businesses b ON b.id = p.business_id WHERE p.id = %s""",
            (product_id,),
        )
        owner_id, product_name = cursor.fetchone()
        return {"id": order_id, "owner_id": owner_id, "product_name": product_name}


async def create_order(product_id: int, customer: dict[str, str]) -> dict[str, Any]:
    return await asyncio.to_thread(_create_order, product_id, customer)


def _list_businesses() -> list[dict[str, Any]]:
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM businesses ORDER BY name")
        return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]


async def list_businesses() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_businesses)


def _get_business(slug: str) -> dict[str, Any] | None:
    with connect(_require_database()) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, name, slug FROM businesses WHERE slug = %s", (slug,))
        row = cursor.fetchone()
        return {"id": row[0], "name": row[1], "slug": row[2]} if row else None


async def get_business(slug: str) -> dict[str, Any] | None:
    return await asyncio.to_thread(_get_business, slug)
