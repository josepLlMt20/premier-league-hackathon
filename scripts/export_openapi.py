"""Export public contracts without starting ingestion or authenticating to Azure."""
import argparse
import json
from pathlib import Path

from match_context.api.app import create_app
from match_context.config import Settings
from match_context.storage.sqlite import SQLiteEventLog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("web/openapi.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    log = SQLiteEventLog(":memory:")
    try:
        schema = create_app(Settings(), log).openapi()
    finally:
        log.close()
    text = json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != text:
            raise SystemExit("Public OpenAPI is out of date")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
