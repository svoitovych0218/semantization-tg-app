from openai import OpenAI

from .config import settings

_client: OpenAI | None = None
MODEL = "text-embedding-3-small"


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def encode_query(word: str) -> list[float]:
    response = get_client().embeddings.create(input=word, model=MODEL)
    return response.data[0].embedding


def warm_up() -> None:
    get_client()
