import unittest
from datetime import date
from trend_research import validate_dossier


def sample():
    return {
        "topic": "Example technology story",
        "editorial_angle": "What changed and why it matters",
        "discovery_timestamp": "2026-11-08T10:00:00+02:00",
        "sources": [
            {"id": "a", "url": "https://news.example.com/story",
             "publisher": "Example News", "published_at": "2026-11-07",
             "source_type": "independent"},
            {"id": "b", "url": "https://research.example.org/report",
             "publisher": "Example Research", "published_at": "2026-11-08",
             "source_type": "primary"},
        ],
        "claims": [{"text": "A material claim", "source_ids": ["a", "b"],
                    "status": "verified"}],
    }


class TrendDossierTests(unittest.TestCase):
    def test_valid_dossier(self):
        result = validate_dossier(sample(), today=date(2026, 11, 8))
        self.assertTrue(result["valid"])
        self.assertEqual(result["source_count"], 2)

    def test_rejects_single_source(self):
        d = sample()
        d["sources"] = d["sources"][:1]
        with self.assertRaisesRegex(ValueError, "two sources"):
            validate_dossier(d, today=date(2026, 11, 8))

    def test_rejects_same_domain_as_independent(self):
        d = sample()
        d["sources"][1]["url"] = "https://news.example.com/another"
        with self.assertRaisesRegex(ValueError, "independent source domains"):
            validate_dossier(d, today=date(2026, 11, 8))

    def test_rejects_stale_source(self):
        d = sample()
        d["sources"][0]["published_at"] = "2026-10-01"
        with self.assertRaisesRegex(ValueError, "stale source"):
            validate_dossier(d, today=date(2026, 11, 8))

    def test_rejects_http(self):
        d = sample()
        d["sources"][0]["url"] = "http://news.example.com/story"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_dossier(d, today=date(2026, 11, 8))

    def test_rejects_unknown_reference(self):
        d = sample()
        d["claims"][0]["source_ids"] = ["a", "missing"]
        with self.assertRaisesRegex(ValueError, "unknown source"):
            validate_dossier(d, today=date(2026, 11, 8))

    def test_rejects_timezone_free_timestamp(self):
        d = sample()
        d["discovery_timestamp"] = "2026-11-08T10:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_dossier(d, today=date(2026, 11, 8))


if __name__ == "__main__":
    unittest.main()
