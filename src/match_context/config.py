"""Server-owned configuration. Factual mode never needs an Azure credential."""

import os
from typing import Literal, Mapping

from pydantic import Field, model_validator
from match_context.domain.events import FrozenModel


class Settings(FrozenModel):
    app_env: Literal["development", "test", "production"] = "development"
    storage_backend: Literal["sqlite", "azure_tables"] = "sqlite"
    agent_mode: Literal["factual", "scripted", "foundry"] = "factual"
    foundry_project_endpoint: str | None = None
    foundry_model: str | None = None
    azure_table_endpoint: str | None = None
    azure_client_id: str | None = None
    max_model_calls: int = Field(default=7, ge=1, le=7)
    max_tool_calls: int = Field(default=8, ge=1, le=8)
    max_output_tokens: int = Field(default=1200, ge=1, le=1200)
    context_timeout_seconds: float = Field(default=10, gt=0, le=10)
    cache_capacity: int = Field(default=128, ge=1, le=128)
    max_concurrent_generations: int = Field(default=2, ge=1, le=2)

    @model_validator(mode="after")
    def configured_mode(self):
        if self.agent_mode == "foundry" and (not self.foundry_project_endpoint or not self.foundry_model):
            raise ValueError("Foundry requires project endpoint and deployment")
        if self.agent_mode == "scripted" and self.app_env == "production":
            raise ValueError("Scripted mode is only available in development or test")
        if self.storage_backend == "azure_tables" and not self.azure_table_endpoint:
            raise ValueError("Azure Tables requires an endpoint")
        return self

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None):
        values = os.environ if env is None else env
        return cls(**{name: values[name.upper()] for name in cls.model_fields if name.upper() in values})
