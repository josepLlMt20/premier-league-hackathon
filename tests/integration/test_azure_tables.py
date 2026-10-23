import pytest
from azure.core.exceptions import AzureError

from match_context.storage.base import ConcurrentWrite


def test_lost_success_response_is_resolved_without_double_append(azure_log, metadata, make_event):
    log, transport = azure_log
    log.register_match(metadata)
    transport.lose_batch_response = True
    assert log.append(make_event()) is True
    assert log.head("match-1") == 1
    assert log.append(make_event()) is False
    assert log.read_through("match-1", 1) == (make_event(),)


def test_failed_transaction_leaves_no_event_or_advanced_header(azure_log, metadata, make_event):
    log, transport = azure_log
    log.register_match(metadata)
    transport.fail_batch = True
    with pytest.raises(AzureError):
        log.append(make_event())
    transport.fail_batch = False
    assert log.head("match-1") == 0
    assert log.append(make_event()) is True


def test_stale_header_etag_cannot_commit_partial_event(azure_log, metadata, make_event):
    log, transport = azure_log
    log.register_match(metadata)
    transport.race_batch = True
    with pytest.raises(ConcurrentWrite):
        log.append(make_event())
    assert log.head("match-1") == 0
    assert log.append(make_event()) is True
