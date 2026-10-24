import pytest
from match_context.domain.contracts import ContextRequest


def test_cache_keys_separate_every_request_preference_and_snapshot():
    from match_context.service.cache import ContextCache
    request = ContextRequest(match_id="one", from_sequence=0, to_sequence=10)
    baseline = ContextCache.key(request, "prefix-one")
    changes = ({"match_id": "two"}, {"from_sequence": 1}, {"to_sequence": 9}, {"role": "commentator"},
               {"depth": "detailed"}, {"language": "en"}, {"favorite_team_id": "amber"})
    assert len({baseline, *(ContextCache.key(request.model_copy(update=change), "prefix-one")
                            for change in changes), ContextCache.key(request, "prefix-two")}) == 9


def test_lru_is_bounded_and_cache_restart_is_empty():
    from match_context.service.cache import ContextCache
    cache = ContextCache(capacity=2)
    cache.put("one", 1)
    cache.put("two", 2)
    assert cache.get("one") == 1
    cache.put("three", 3)
    assert cache.get("two") is None
    assert cache.get("one") == 1 and cache.get("three") == 3
    assert len(cache) == 2 and len(ContextCache()) == 0
    with pytest.raises(ValueError):
        ContextCache(capacity=129)
