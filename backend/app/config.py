"""Application configuration.

Centralises every environment variable the backend reads. Notably this fixes the
original bug where the code read ``GCP_LOCATION`` while the ``.env`` file defined
``GOOGLE_LOCATION`` — both names are now accepted (``GCP_LOCATION`` preferred).
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parents[2] is the repository root (Professionally-You/).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Prefer a local backend/.env, fall back to the repo-root .env.
        env_file=(".env", str(_REPO_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),  # allow a field literally named ``model_name``
    )

    # --- Google Cloud / Vertex AI ---
    gcp_project: str | None = Field(default=None, validation_alias="GCP_PROJECT")
    # Accept either GCP_LOCATION (preferred) or the legacy GOOGLE_LOCATION name.
    gcp_location: str = Field(
        default="us-central1",
        validation_alias=AliasChoices("GCP_LOCATION", "GOOGLE_LOCATION"),
    )
    model_name: str = Field(
        default="google/gemini-2.5-pro", validation_alias="MODEL_NAME"
    )

    # --- Persona ---
    person_name: str = Field(default="Allen Diaz", validation_alias="PERSON_NAME")
    me_dir: Path = Field(default=_REPO_ROOT / "me", validation_alias="ME_DIR")

    # --- RAG / profile ---
    # Where the editable profile.json and the RAG index are persisted.
    data_dir: Path = Field(
        default=_REPO_ROOT / "backend" / "data", validation_alias="DATA_DIR"
    )
    embedding_model: str = Field(
        default="text-embedding-004", validation_alias="EMBEDDING_MODEL"
    )
    rag_top_k: int = Field(default=4, validation_alias="RAG_TOP_K")
    rag_chunk_size: int = Field(default=800, validation_alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=150, validation_alias="RAG_CHUNK_OVERLAP")

    # --- Database ---
    # SQLite by default for local/dev; set DATABASE_URL to a Postgres URL in prod,
    # e.g. postgresql+psycopg://user:pass@host:5432/dbname
    database_url: str = Field(
        default=f"sqlite:///{_REPO_ROOT / 'backend' / 'data' / 'app.db'}",
        validation_alias="DATABASE_URL",
    )

    # --- Admin API ---
    # Bearer token that guards /api/admin/*. If unset, the admin API returns 503.
    admin_token: str | None = Field(default=None, validation_alias="ADMIN_TOKEN")

    # --- Pushover ---
    pushover_user: str | None = Field(default=None, validation_alias="PUSHOVER_USER")
    pushover_token: str | None = Field(default=None, validation_alias="PUSHOVER_TOKEN")

    # --- Chat behaviour ---
    # Hard cap on the tool-calling loop so a misbehaving model can't loop forever.
    max_tool_iterations: int = Field(default=6, validation_alias="MAX_TOOL_ITERATIONS")

    # --- Guardrails / evaluator ---
    # Both fail open (never block a reply) if the check itself errors. Off switches
    # are provided since each adds an extra LLM round-trip's worth of latency/cost.
    enable_guardrails: bool = Field(default=True, validation_alias="ENABLE_GUARDRAILS")
    enable_evaluator: bool = Field(default=True, validation_alias="ENABLE_EVALUATOR")

    # --- Rate limiting ---
    # slowapi limit string, e.g. "20/minute". Applied per client IP to /api/chat*.
    chat_rate_limit: str = Field(default="20/minute", validation_alias="CHAT_RATE_LIMIT")

    # --- CORS ---
    allowed_origins: str = Field(
        default="http://localhost:3000", validation_alias="ALLOWED_ORIGINS"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def vertex_base_url(self) -> str:
        return (
            f"https://{self.gcp_location}-aiplatform.googleapis.com/v1"
            f"/projects/{self.gcp_project}/locations/{self.gcp_location}/endpoints/openapi"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
