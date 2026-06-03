from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
MODEL_NAME = "intfloat/multilingual-e5-small"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def encode_passage(word: str) -> list[float]:
    """Embed a secret word using the passage: prefix required by e5 models."""
    vec = get_model().encode(f"passage: {word}", normalize_embeddings=True)
    return vec.tolist()


def warm_up() -> None:
    """Pre-load the model at startup so the first request is not slow."""
    get_model()
