from dataclasses import replace

import pytest
from tests.unit.domain.normative.fire_evidence.factories import facility


@pytest.mark.parametrize("value", ["short", "AB" * 32, "zz" * 32])
def test_invalid_document_hash_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="SHA256"):
        replace(facility(), source_sha256=value)
