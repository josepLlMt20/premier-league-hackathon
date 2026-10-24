"""Offline HTTP boundary for the real Azure Tables SDK, not an Azure emulator."""

from copy import deepcopy
from email import policy
from email.parser import BytesParser
import json
import re
from urllib.parse import parse_qs, unquote, urlparse

from azure.core.exceptions import ServiceResponseError
from azure.core.pipeline.transport import HttpResponse, HttpTransport


class Response(HttpResponse):
    def __init__(self, request, status, body=b"", headers=None):
        super().__init__(request, None)
        self.status_code = status
        self.reason = "offline test response"
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.content_type = self.headers["Content-Type"]
        self._body = body

    def body(self):
        return self._body


class TablesTransport(HttpTransport):
    def __init__(self):
        self.rows = {}
        self.page_size = 3
        self.lose_batch_response = False
        self.fail_batch = False
        self.race_batch = False

    def open(self):
        pass

    def close(self):
        pass

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def error(request, status, code):
        return Response(request, status, json.dumps({"odata.error": {
            "code": code, "message": {"lang": "en-US", "value": code},
        }}).encode())

    def send(self, request, **kwargs):
        if request.url.endswith("/$batch"):
            return self.batch(request)
        parsed = urlparse(request.url)
        key_match = re.search(r"PartitionKey='([^']+)',RowKey='([^']+)'", unquote(parsed.path))
        if request.method == "GET" and key_match:
            row = self.rows.get(key_match.groups())
            if row is None:
                return self.error(request, 404, "ResourceNotFound")
            return Response(request, 200, json.dumps(row).encode(), {"ETag": row["odata.etag"]})
        if request.method == "GET":
            query = parse_qs(parsed.query)
            expression = query["$filter"][0]
            if expression == "RowKey eq '!head'":
                cursor = (query.get("NextPartitionKey", [""])[0], query.get("NextRowKey", [""])[0])
                rows = [value for key, value in sorted(self.rows.items()) if key[1] == "!head" and key >= cursor]
                headers = {}
                if len(rows) > self.page_size:
                    next_row = rows[self.page_size]
                    headers = {"x-ms-continuation-NextPartitionKey": next_row["PartitionKey"],
                               "x-ms-continuation-NextRowKey": next_row["RowKey"]}
                return Response(request, 200, json.dumps({"value": rows[:self.page_size]}).encode(), headers)
            partition = re.search(r"PartitionKey eq '([^']+)'", expression).group(1)
            lower = re.search(r"RowKey ge '([^']+)'", expression).group(1)
            upper = re.search(r"RowKey le '([^']+)'", expression).group(1)
            continuation = query.get("NextRowKey", [""])[0]
            rows = [v for (pk, rk), v in sorted(self.rows.items())
                    if pk == partition and lower <= rk <= upper and rk >= continuation]
            page = rows[:self.page_size]
            headers = {}
            if len(rows) > self.page_size:
                headers = {"x-ms-continuation-NextPartitionKey": partition,
                           "x-ms-continuation-NextRowKey": rows[self.page_size]["RowKey"]}
            return Response(request, 200, json.dumps({"value": page}).encode(), headers)
        entity = json.loads(request.body)
        key = (entity["PartitionKey"], entity["RowKey"])
        if request.method == "POST" and key in self.rows:
            return self.error(request, 409, "EntityAlreadyExists")
        if request.method == "PUT" and request.headers.get("If-Match") != self.rows[key]["odata.etag"]:
            return self.error(request, 412, "UpdateConditionNotSatisfied")
        previous = self.rows.get(key, {})
        entity["odata.etag"] = f'W/"{int(previous.get("_version", 0)) + 1}"'
        entity["_version"] = int(previous.get("_version", 0)) + 1
        self.rows[key] = entity
        return Response(request, 204, headers={"ETag": entity["odata.etag"]})

    def batch(self, request):
        message = BytesParser(policy=policy.default).parsebytes(
            f'Content-Type: {request.headers["Content-Type"]}\r\n\r\n'.encode() + request.body)
        operations = []
        for part in message.walk():
            if part.get_content_type() != "application/http":
                continue
            raw = part.get_payload(decode=True).decode()
            header, body = raw.split("\r\n\r\n", 1)
            method = header.split(" ", 1)[0]
            entity = json.loads(body)
            etag_match = re.search(r"(?im)^If-Match: (.+)$", header)
            operations.append((method, entity, etag_match.group(1).strip() if etag_match else None))
        if self.race_batch:
            self.race_batch = False
            key = (operations[-1][1]["PartitionKey"], operations[-1][1]["RowKey"])
            self.rows[key]["odata.etag"] = 'W/"changed-concurrently"'
        draft = deepcopy(self.rows)
        results = []
        for index, (method, entity, etag) in enumerate(operations):
            key = (entity["PartitionKey"], entity["RowKey"])
            status = 204
            code = None
            if method == "POST" and key in draft:
                status, code = 409, "EntityAlreadyExists"
            elif method == "PUT" and etag != draft[key]["odata.etag"]:
                status, code = 412, "UpdateConditionNotSatisfied"
            elif self.fail_batch:
                status, code = 503, "ServerBusy"
            if code:
                results = [(index, status, json.dumps({"odata.error": {
                    "code": code, "message": {"lang": "en-US", "value": f"{index}:{code}"},
                }}), None)]
                break
            version = int(draft.get(key, {}).get("_version", 0)) + 1
            entity.update({"odata.etag": f'W/"{version}"', "_version": version})
            draft[key] = entity
            results.append((index, 204, "", entity["odata.etag"]))
        else:
            self.rows = draft
            if self.lose_batch_response:
                self.lose_batch_response = False
                raise ServiceResponseError("Committed but response was lost")
        pieces = ["--batchresponse\r\nContent-Type: multipart/mixed; boundary=changesetresponse\r\n\r\n"]
        for index, status, body, etag in results:
            pieces.append(f"--changesetresponse\r\nContent-Type: application/http\r\nContent-Transfer-Encoding: binary\r\nContent-ID: {index}\r\n\r\nHTTP/1.1 {status} offline\r\nContent-Type: application/json\r\n")
            if etag:
                pieces.append(f"ETag: {etag}\r\n")
            pieces.append(f"\r\n{body}\r\n")
        pieces.append("--changesetresponse--\r\n--batchresponse--\r\n")
        return Response(request, 202, "".join(pieces).encode(),
                        {"Content-Type": "multipart/mixed; boundary=batchresponse"})
