import os
import tempfile
import unittest
from unittest import mock

import jarvis_config as cfg


class ConfigTests(unittest.TestCase):
    def test_env_helpers_and_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {
                "JARVIS_AI_DATA_DIR": tmpdir,
                "JARVIS_SETTINGS_FILE": os.path.join(tmpdir, "settings.custom.json"),
                "JARVIS_ENV_FILE": os.path.join(tmpdir, ".env.custom"),
                "JARVIS_MEMORY_DB": os.path.join(tmpdir, "memory.custom.db"),
                "JARVIS_PLUGIN_DAILY_LIMIT": "31",
                "JARVIS_TOOL_TIMEOUT_SECONDS": "12.5",
                "JARVIS_DEFAULT_CITY": "Berlin",
                "JARVIS_FEATURE_MEMORY_DIGEST": "yes",
            }
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertEqual(cfg.ai_data_dir(), tmpdir)
                self.assertEqual(cfg.settings_file(), env["JARVIS_SETTINGS_FILE"])
                self.assertEqual(cfg.env_file(), env["JARVIS_ENV_FILE"])
                self.assertEqual(cfg.memory_db_file(), env["JARVIS_MEMORY_DB"])
                self.assertEqual(cfg.plugin_daily_limit(), 31)
                self.assertAlmostEqual(cfg.tool_timeout_seconds(), 12.5)
                self.assertEqual(cfg.default_city(), "Berlin")
                self.assertTrue(cfg.feature_enabled("memory_digest"))


if __name__ == "__main__":
    unittest.main()
