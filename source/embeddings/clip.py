"""Local CLIP image embeddings; model weights download once on first use."""

import asyncio
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_clip():
    """Load once from the local Hugging Face cache; never call an embedding API."""
    from transformers import CLIPModel, CLIPProcessor

    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name, local_files_only=True)
    processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
    model.eval()
    return model, processor


def _embed_image(image_path: str) -> list[float]:
    import torch
    from PIL import Image

    model, processor = _load_clip()
    with Image.open(image_path) as image:
        inputs = processor(images=image.convert("RGB"), return_tensors="pt")
    with torch.no_grad():
        embedding = _feature_tensor(model.get_image_features(**inputs)).flatten()
        embedding = embedding / embedding.norm(p=2)
    if embedding.numel() != 512:
        raise RuntimeError(f"CLIP returned {embedding.numel()} values; expected 512")
    return embedding.tolist()


async def embed_image(image_path: str | Path) -> list[float]:
    """Produce a normalized 512-dimensional embedding without an embedding API."""
    return await asyncio.to_thread(_embed_image, str(image_path))


def _feature_tensor(output):
    """Support Transformers releases returning either a Tensor or ModelOutput."""
    if hasattr(output, "pooler_output"):
        return output.pooler_output
    if hasattr(output, "image_embeds"):
        return output.image_embeds
    if hasattr(output, "text_embeds"):
        return output.text_embeds
    return output


def _embed_text(text: str) -> list[float]:
    import torch

    model, processor = _load_clip()
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        embedding = _feature_tensor(model.get_text_features(**inputs)).flatten()
        embedding = embedding / embedding.norm(p=2)
    return embedding.tolist()


async def embed_text(text: str) -> list[float]:
    """Embed a customer search phrase in the same local CLIP vector space."""
    return await asyncio.to_thread(_embed_text, text)
