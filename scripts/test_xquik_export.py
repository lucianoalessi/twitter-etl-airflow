import json
import tempfile
import unittest
from pathlib import Path

from xquik_export import load_xquik_export_rows


class XquikExportTest(unittest.TestCase):
    def test_load_wrapped_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "tweets.json"
            export_path.write_text(
                json.dumps(
                    {
                        "tweets": [
                            {
                                "author": "crypto",
                                "text": "market update",
                                "likes": 7,
                                "retweets": 2,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                load_xquik_export_rows(export_path),
                [
                    {
                        "user": "crypto",
                        "text": "market update",
                        "favorite_count": 7,
                        "retweet_count": 2,
                        "created_at": "",
                    }
                ],
            )

    def test_load_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "tweets.jsonl"
            export_path.write_text('{"username":"news","full_text":"jsonl row"}\n', encoding="utf-8")

            rows = load_xquik_export_rows(export_path)

            self.assertEqual(rows[0]["user"], "news")
            self.assertEqual(rows[0]["text"], "jsonl row")

    def test_reject_unknown_suffix(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "tweets.txt"
            export_path.write_text("text", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, ".json"):
                load_xquik_export_rows(export_path)


if __name__ == "__main__":
    unittest.main()
