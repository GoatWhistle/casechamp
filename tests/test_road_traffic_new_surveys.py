import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))

from road_traffic.new_surveys import birobidzhan_rows, obninsk_rows


class RoadTrafficNewSurveyTests(unittest.TestCase):
    def obninsk_pages(self):
        pages = [""] * 119
        pages[110] = "в июне 2025 г. видеосъемка утреннего, дневного и вечернего пиков"
        pages[111] = "\n".join(
            f"{site}  ул. Первая - ул. Вторая" for site in range(1, 23)
        )
        pages[118] = "Таблица 1.8.4 -\n" + "\n".join(
            f"{site}  ул. Первая - ул. Вторая  189,6  208  248,4  258,4"
            for site in range(1, 23)
        )
        return pages

    def test_junction_periods_keep_derived_column_out_of_observations(self):
        rows = obninsk_rows(self.obninsk_pages())
        first = [row for row in rows if row["site_id"] == "1"]
        self.assertEqual([row["value"] for row in first], [189.6, 208, 248.4])
        self.assertEqual(len(rows), 66)
        self.assertTrue(
            all(row["measurement_extent"] == "junction_aggregate" for row in rows)
        )
        self.assertTrue(all(row["direction"] == "unknown" for row in rows))
        self.assertEqual(
            first[0]["reported_derived_parameters"][
                "reported_daily_interinterval_intensity"
            ],
            "258,4",
        )
        self.assertTrue(
            all(
                row["assignment_policy"]
                == "do_not_assign_junction_total_to_individual_roads"
                for row in rows
            )
        )

    def test_partial_table_does_not_silently_reduce_sample(self):
        pages = self.obninsk_pages()
        pages[118] = pages[118].rsplit("\n", 1)[0]
        with self.assertRaisesRegex(ValueError, "22 Obninsk"):
            obninsk_rows(pages)

    def test_birobidzhan_coordinate_pairing_and_unresolved_direction(self):
        pages = [""] * 80
        pages[77] = "Таблица 5 –\n" + "\n".join(
            f"Биробиджан, Еврейская автономная область,\n {site}  48.810275, 132.881162\n Россия, ул. Шолом-Алейхема"
            for site in range(1, 11)
        )
        pages[78] = "Таблица 6 –\n" + "\n".join(f"{site}  574" for site in range(1, 5))
        pages[79] = "Продолжение таблицы 6\n" + "\n".join(
            f"{site}  611" for site in range(5, 11)
        )
        rows = birobidzhan_rows(pages)
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["lat"], 48.810275)
        self.assertEqual(rows[0]["lon"], 132.881162)
        self.assertEqual(rows[-1]["value"], 611)
        self.assertIn("unspecified", rows[0]["direction"])
        self.assertIn("date unspecified", rows[0]["period"])
        self.assertEqual(rows[0]["measurement_extent"], "road_section_counter")

    def test_changed_document_context_is_rejected(self):
        pages = self.obninsk_pages()
        pages[110] = "forecast"
        with self.assertRaisesRegex(ValueError, "context"):
            obninsk_rows(pages)


if __name__ == "__main__":
    unittest.main()
