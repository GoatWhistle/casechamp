import pytest

from import_national_inventory import insert_batch


class InsertClient:
    def __init__(self, failures: list[str]) -> None:
        self.failures = failures
        self.calls = []

    def request(self, sql: str, payload: bytes) -> bytes:
        self.calls.append((sql, payload))
        if self.failures:
            raise RuntimeError(self.failures.pop(0))
        return b""


def test_memory_pressure_retries_the_same_payload_with_bounded_parallelism(monkeypatch):
    delays = []
    monkeypatch.setattr("import_national_inventory.time.sleep", delays.append)
    client = InsertClient(["MEMORY_LIMIT_EXCEEDED"])
    insert_batch(client, "plexus_normative.national_inventory", ['{"id":"a"}'])
    assert len(client.calls) == 2
    assert client.calls[0] == client.calls[1]
    assert "max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0" in client.calls[0][0]
    assert delays == [2]


def test_invalid_insert_is_not_retried(monkeypatch):
    monkeypatch.setattr("import_national_inventory.time.sleep", lambda delay: pytest.fail("Unexpected retry"))
    client = InsertClient(["UNKNOWN_TABLE"])
    with pytest.raises(RuntimeError, match="UNKNOWN_TABLE"):
        insert_batch(client, "plexus_normative.national_inventory", [])
    assert len(client.calls) == 1


def test_persistent_memory_pressure_fails_after_six_attempts(monkeypatch):
    delays = []
    monkeypatch.setattr("import_national_inventory.time.sleep", delays.append)
    client = InsertClient(["MEMORY_LIMIT_EXCEEDED"] * 6)
    with pytest.raises(RuntimeError, match="MEMORY_LIMIT_EXCEEDED"):
        insert_batch(client, "plexus_normative.national_inventory", [])
    assert len(client.calls) == 6
    assert delays == [2, 4, 8, 16, 30]
