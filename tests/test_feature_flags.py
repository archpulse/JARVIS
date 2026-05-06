import importlib
import os
import tempfile
import unittest
from unittest import mock


def reload_plugin(module_name: str):
    module = importlib.import_module(module_name)
    return importlib.reload(module)


class FeatureFlagRegistrationTests(unittest.TestCase):
    def test_memory_digest_flag_controls_registration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(
                os.environ,
                {
                    "JARVIS_AI_DATA_DIR": tmpdir,
                    "JARVIS_FEATURE_MEMORY_DIGEST": "1",
                },
                clear=False,
            ):
                mod = reload_plugin("plugins.p00_core_memory")
                tools, mapping = mod.register_plugin()
                self.assertIn("get_memory_digest", mapping)
                self.assertIn(mod.get_memory_digest, tools)

            with mock.patch.dict(
                os.environ,
                {
                    "JARVIS_AI_DATA_DIR": tmpdir,
                    "JARVIS_FEATURE_MEMORY_DIGEST": "0",
                },
                clear=False,
            ):
                mod = reload_plugin("plugins.p00_core_memory")
                tools, mapping = mod.register_plugin()
                self.assertNotIn("get_memory_digest", mapping)
                self.assertNotIn(mod.get_memory_digest, tools)

    def test_system_snapshot_flag_controls_registration(self):
        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_SYSTEM_SNAPSHOT": "1"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p08_system_info_pro")
            tools, mapping = mod.register_plugin()
            self.assertIn("get_system_snapshot", mapping)
            self.assertIn(mod.get_system_snapshot, tools)

        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_SYSTEM_SNAPSHOT": "0"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p08_system_info_pro")
            tools, mapping = mod.register_plugin()
            self.assertNotIn("get_system_snapshot", mapping)

    def test_city_briefing_flag_controls_registration(self):
        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_CITY_BRIEFING": "1"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p01_core_system")
            tools, mapping = mod.register_plugin()
            self.assertIn("get_city_briefing", mapping)
            self.assertIn(mod.get_city_briefing, tools)

        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_CITY_BRIEFING": "0"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p01_core_system")
            tools, mapping = mod.register_plugin()
            self.assertNotIn("get_city_briefing", mapping)


if __name__ == "__main__":
    unittest.main()
