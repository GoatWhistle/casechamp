from dataclasses import replace

import pytest

from app.domain.normative.model import Facility
from import_regional_directories import directory_memberships


def facility() -> Facility:
    return Facility('a', 'employment', 'Office', 'Address', 'https://example.org/directory', '2026-11-12', None, None, None, 'missing', source_sha256='a' * 64)


def registration() -> dict:
    return {'region_id': 'R', 'category': 'employment_candidate', 'service': 'employment', 'scope_source_url': 'https://example.org/directory', 'scope_source_sha256': 'a' * 64, 'facility_ids': ['a']}


def test_explicit_memberships_keep_an_unknown_coordinate_without_inventing_it():
    rows = directory_memberships([registration()], [facility()], {'R'})
    assert rows == [{'region_id': 'R', 'category': 'employment_candidate', 'facility_id': 'a', 'service': 'employment', 'scope_source_url': facility().source_url, 'scope_source_sha256': facility().source_sha256}]


@pytest.mark.parametrize('change', [{'region_id': 'Other'}, {'category': 'other'}, {'facility_ids': ['missing']}, {'facility_ids': ['a', 'a']}, {'scope_source_sha256': 'b' * 64}, {'scope_source_url': 'https://example.org/other'}])
def test_missing_or_misassigned_directory_inputs_are_rejected_before_publication(change):
    with pytest.raises(ValueError):
        directory_memberships([{**registration(), **change}], [facility()], {'R'})


def test_a_directory_membership_requires_the_primary_source_digest():
    with pytest.raises(ValueError):
        directory_memberships([registration()], [replace(facility(), source_sha256=None)], {'R'})
