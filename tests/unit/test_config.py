import pytest
from pydantic import ValidationError


def test_factual_configuration_needs_no_azure_and_reads_only_known_env():
    from match_context.config import Settings
    settings = Settings.from_env({"AGENT_MODE": "factual", "MAX_MODEL_CALLS": "5", "UNRELATED_SECRET": "private"})
    assert settings.agent_mode == "factual" and settings.max_model_calls == 5
    assert "private" not in settings.model_dump_json()


@pytest.mark.parametrize("values", [
    {"agent_mode": "foundry"}, {"agent_mode": "scripted", "app_env": "production"},
    {"max_model_calls": 8}, {"max_tool_calls": 9}, {"context_timeout_seconds": 26},
    {"max_output_tokens": 1201}, {"cache_capacity": 129}, {"max_concurrent_generations": 3},
    {"context_timeout_seconds": float("nan")}, {"storage_backend": "azure_tables"},
])
def test_invalid_modes_missing_configuration_and_relaxed_limits_fail(values):
    from match_context.config import Settings
    with pytest.raises(ValidationError):
        Settings(**values)


def test_foundry_configuration_accepts_existing_resource_without_provisioning():
    from match_context.config import Settings
    settings = Settings.from_env({"AGENT_MODE": "foundry", "FOUNDRY_PROJECT_ENDPOINT":
        "https://offline.services.ai.azure.com/api/projects/test", "FOUNDRY_MODEL": "existing"})
    assert settings.foundry_model == "existing"


def test_generation_deadline_is_long_enough_for_three_roles_but_remains_bounded():
    from match_context.config import Settings
    from match_context.agents.base import AgentLimits
    assert Settings().context_timeout_seconds == AgentLimits().deadline_seconds == 25
    assert Settings.from_env({"CONTEXT_TIMEOUT_SECONDS": "20"}).context_timeout_seconds == 20
    for value in (26, float("inf"), float("nan")):
        with pytest.raises(ValidationError):
            Settings(context_timeout_seconds=value)
        with pytest.raises(ValidationError):
            AgentLimits(deadline_seconds=value)
