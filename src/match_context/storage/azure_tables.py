from azure.core import MatchConditions
from azure.core.exceptions import AzureError, ResourceExistsError, ResourceNotFoundError
from azure.data.tables import TableClient, UpdateMode

from match_context.domain.events import MatchEvent, MatchMetadata
from .base import (ConcurrentWrite, CorruptEventLog, EventConflict, EventLog, IngestPosition,
                   MatchNotFound, check_integer, prepare_append)

HEADER_KEY = "!head"


class AzureTableEventLog(EventLog):
    """Uses an existing MatchEvents table; the caller owns credentials and provisioning."""

    def __init__(self, client: TableClient):
        self._client = client

    def _header(self, match_id):
        try:
            return self._client.get_entity(match_id, HEADER_KEY)
        except ResourceNotFoundError as error:
            raise MatchNotFound(match_id) from error

    def register_match(self, metadata: MatchMetadata) -> bool:
        metadata = MatchMetadata.model_validate(metadata.model_dump())
        entity = {"PartitionKey": metadata.match_id, "RowKey": HEADER_KEY,
                  "Metadata": metadata.model_dump_json(), "Sequence": 0, "Clock": 0}
        try:
            self._client.create_entity(entity)
            return True
        except AzureError as error:
            try:
                stored = self.metadata(metadata.match_id)
            except (AzureError, MatchNotFound):
                raise error
            if stored != metadata:
                raise EventConflict("Match metadata is immutable") from error
            return not isinstance(error, ResourceExistsError)

    def metadata(self, match_id: str) -> MatchMetadata:
        return MatchMetadata.model_validate_json(self._header(match_id)["Metadata"])

    def list_matches(self) -> tuple[MatchMetadata, ...]:
        rows = self._client.query_entities("RowKey eq @header", parameters={"header": HEADER_KEY}, select=["Metadata"])
        return tuple(sorted((MatchMetadata.model_validate_json(row["Metadata"]) for row in rows),
                            key=lambda metadata: metadata.match_id))

    def position(self, match_id: str) -> IngestPosition:
        header = self._header(match_id)
        return IngestPosition(header["Sequence"], header["Clock"])

    def _read(self, match_id, cutoff):
        if cutoff == 0:
            return ()
        rows = self._client.query_entities(
            "PartitionKey eq @match and RowKey ge @first and RowKey le @last",
            parameters={"match": match_id, "first": "000000000001", "last": f"{cutoff:012d}"})
        events = tuple(sorted((MatchEvent.model_validate_json(row["Payload"]) for row in rows),
                              key=lambda event: event.sequence))
        if len(events) != cutoff or any(event.match_id != match_id or event.sequence != index
                                       for index, event in enumerate(events, 1)):
            raise CorruptEventLog("Stored history does not match its committed prefix")
        return events

    def read_through(self, match_id: str, cutoff: int) -> tuple[MatchEvent, ...]:
        check_integer(cutoff)
        header = self._header(match_id)
        return self._read(match_id, min(cutoff, header["Sequence"]))

    def append(self, event: MatchEvent) -> bool:
        header = self._header(event.match_id)
        prefix = self._read(event.match_id, header["Sequence"])
        if not prepare_append(event, MatchMetadata.model_validate_json(header["Metadata"]), prefix,
                              IngestPosition(header["Sequence"], header["Clock"])):
            return False
        entity = {"PartitionKey": event.match_id, "RowKey": f"{event.sequence:012d}",
                  "Payload": event.model_dump_json()}
        update = dict(header)
        update.update({"Sequence": event.sequence, "Clock": event.available_second})
        try:
            self._client.submit_transaction([
                ("create", entity),
                ("update", update, {"mode": UpdateMode.REPLACE, "etag": header.metadata["etag"],
                                     "match_condition": MatchConditions.IfNotModified}),
            ])
        except AzureError as error:
            # A timeout may hide a committed transaction. Read its key before any retry.
            try:
                stored = self._client.get_entity(event.match_id, entity["RowKey"])
                committed = MatchEvent.model_validate_json(stored["Payload"])
                if committed != event:
                    raise EventConflict("Concurrent write committed a different event") from error
                if self.head(event.match_id) >= event.sequence:
                    return True
            except ResourceNotFoundError:
                pass
            except AzureError:
                raise error
            if getattr(error, "status_code", None) in (409, 412):
                raise ConcurrentWrite("Header changed while appending") from error
            raise
        return True

    def advance_clock(self, match_id: str, available_second: int) -> None:
        check_integer(available_second, 5400)
        header = self._header(match_id)
        if available_second < header["Clock"]:
            raise ValueError("Ingestion clock cannot rewind")
        if available_second == header["Clock"]:
            return
        update = dict(header)
        update["Clock"] = available_second
        try:
            self._client.update_entity(update, mode=UpdateMode.REPLACE, etag=header.metadata["etag"],
                                       match_condition=MatchConditions.IfNotModified)
        except AzureError as error:
            try:
                if self.position(match_id).available_second >= available_second:
                    return
            except AzureError:
                raise error
            if getattr(error, "status_code", None) == 412:
                raise ConcurrentWrite("Header changed while advancing clock") from error
            raise

    def close(self) -> None:
        self._client.close()
