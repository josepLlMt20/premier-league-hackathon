from match_context.domain.events import FrozenModel


class ScenarioManifest(FrozenModel):
    scenario: str
    seed: int
    baseline_seconds: tuple[int, int] = (900, 1200)
    focus_seconds: tuple[int, int] = (1200, 1500)
    expected_patterns: tuple[str, ...]


def scenario_manifest(scenario: str) -> ScenarioManifest:
    """Evaluation-only expectations. Never insert these into snapshots or agent input."""
    manifests = {
        "main": (7, ("high_recoveries", "chance_quality")),
        "neutral": (11, ()),
        "sterile": (19, ("territorial_shift",)),
        "correction": (23, ("high_recoveries", "chance_quality")),
    }
    if scenario not in manifests:
        raise ValueError("Unknown synthetic scenario")
    seed, patterns = manifests[scenario]
    return ScenarioManifest(scenario=scenario, seed=seed, expected_patterns=patterns)
