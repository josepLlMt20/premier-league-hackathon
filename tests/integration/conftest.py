from azure.core.credentials import AzureNamedKeyCredential
from azure.data.tables import TableClient
import pytest

from match_context.storage.azure_tables import AzureTableEventLog
from match_context.storage.sqlite import SQLiteEventLog
from .fake_tables import TablesTransport


@pytest.fixture(params=["sqlite", "azure"])
def log_factory(request, tmp_path):
    transport = TablesTransport()
    opened = []

    def create():
        if request.param == "sqlite":
            log = SQLiteEventLog(tmp_path / "events.sqlite3")
        else:
            client = TableClient("https://offline.table.core.windows.net", "MatchEvents",
                                 credential=AzureNamedKeyCredential("offline", "YQ=="),
                                 transport=transport, retry_total=0)
            log = AzureTableEventLog(client)
        opened.append(log)
        return log

    yield create
    for log in opened:
        log.close()


@pytest.fixture
def azure_log():
    transport = TablesTransport()
    client = TableClient("https://offline.table.core.windows.net", "MatchEvents",
                         credential=AzureNamedKeyCredential("offline", "YQ=="),
                         transport=transport, retry_total=0)
    log = AzureTableEventLog(client)
    yield log, transport
    log.close()
