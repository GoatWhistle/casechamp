import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from road_traffic.observations import kuzbass_observations, number, observation
from road_traffic.source_discovery import owners_for_regions


class RoadTrafficSourceTests(unittest.TestCase):
    def test_textual_kilometre_counter_is_preserved(self):
        namespace = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        shared = f"<sst {namespace}><si><t>2023; snapshot 2026</t></si><si><t>road (обратное направление)</t></si><si><t>189+620</t></si></sst>"
        sheet = f'<worksheet {namespace}><sheetData><row r="2"><c r="A2" t="s"><v>0</v></c></row><row r="6"/><row r="8"><c r="A8" t="s"><v>1</v></c></row><row r="9"><c r="A9" t="s"><v>2</v></c><c r="F9"><v>10</v></c><c r="S9"><v>10</v></c></row></sheetData></worksheet>'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xlsx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("xl/sharedStrings.xml", shared)
                archive.writestr("xl/worksheets/sheet1.xml", sheet)
            rows = kuzbass_observations(path)
        total = next(row for row in rows if row["source_locator"].endswith("S9"))
        self.assertEqual(total["value"], 10)
        self.assertEqual(total["counter_km_raw"], "189+620")
        self.assertEqual(total["road_name"], "road")
        self.assertEqual(total["direction"], "reported reverse corridor direction")
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(row["value"] is not None for row in rows), 2)

    def test_missing_values_are_not_zero(self):
        for value in ["", "-", "—", "nan", "inf", "-1", "unknown"]:
            self.assertIsNone(number(value))
        self.assertEqual(number("0"), 0)
        self.assertEqual(number("1,5"), 1.5)

    def test_observation_identity_preserves_direction_and_class(self):
        args = (
            "source",
            "32000000",
            "site",
            "unknown",
            "vehicles/day",
            "-",
            "A1",
            "unresolved",
        )
        first = observation(*args)
        self.assertIsNone(first["value"])
        self.assertEqual(first["raw_value"], "-")
        self.assertNotEqual(
            first["observation_id"],
            observation(*args, direction="forward")["observation_id"],
        )
        self.assertNotEqual(
            first["observation_id"],
            observation(*args, vehicle="truck")["observation_id"],
        )

    def test_every_atlas_region_has_official_owner_provenance(self):
        root = Path(__file__).resolve().parents[2]
        rows = owners_for_regions(root, root / "datasets/additional/road-traffic")
        self.assertEqual(len(rows), 82)
        self.assertEqual(len({row["region_id"] for row in rows}), 82)
        self.assertTrue(all(row["owner_url"].startswith("http") for row in rows))
        self.assertTrue(
            all(
                row["owner_provenance"] == "https://www.mintrans.gov.ru/activities"
                for row in rows
            )
        )


if __name__ == "__main__":
    unittest.main()
