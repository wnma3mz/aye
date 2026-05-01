import json
from pathlib import Path
import tempfile
import unittest

from consent_pilot.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_custom_rule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "scan_lines": 3,
                        "cooldown_seconds": 2,
                        "rules": [
                            {
                                "name": "custom",
                                "pattern": "confirm with yes",
                                "answer": "yes",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.scan_lines, 3)
        self.assertEqual(config.cooldown_seconds, 2)
        self.assertEqual(config.rules[0].name, "custom")


if __name__ == "__main__":
    unittest.main()
