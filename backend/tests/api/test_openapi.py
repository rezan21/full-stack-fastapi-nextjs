import json
from pathlib import Path

from app.main import app

SPEC_PATH = Path(__file__).parents[2] / "openapi.json"


def test_committed_openapi_spec_is_current() -> None:
    committed = json.loads(SPEC_PATH.read_text())
    current = json.loads(json.dumps(app.openapi()))
    message = "OpenAPI spec is stale: run scripts/generate-client.sh"
    assert committed["paths"] == current["paths"], message
    assert committed["components"] == current["components"], message
