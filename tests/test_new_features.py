import importlib
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock


def reload_plugin(module_name: str):
    module = importlib.import_module(module_name)
    return importlib.reload(module)


class NewFeatureTests(unittest.TestCase):
    def test_memory_digest_summarizes_recent_entries(self):
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
                mod.save_fact("profile", "name", "Alex")
                mod.save_conversation("user", "Remember that I prefer concise answers.")

                digest = mod.get_memory_digest(3)
                self.assertIn("MEMORY DIGEST", digest)
                self.assertIn("[profile] name: Alex", digest)
                self.assertIn("Recent conversation:", digest)

                if getattr(mod, "_memory_conn", None) is not None:
                    mod._memory_conn.close()

    def test_system_snapshot_includes_fake_processes(self):
        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_SYSTEM_SNAPSHOT": "1"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p08_system_info_pro")

            class FakeProcess:
                def __init__(self, pid, name, cpu, mem):
                    self.info = {"pid": pid, "name": name}
                    self._cpu = cpu
                    self._mem = mem

                def cpu_percent(self, interval=None):
                    return self._cpu

                def memory_percent(self):
                    return self._mem

            with mock.patch.object(mod.psutil, "cpu_percent", return_value=12.5), \
                mock.patch.object(mod.psutil, "virtual_memory", return_value=SimpleNamespace(percent=34.5)), \
                mock.patch.object(mod.psutil, "disk_usage", return_value=SimpleNamespace(percent=55.0)), \
                mock.patch.object(mod.psutil, "net_io_counters", return_value=SimpleNamespace(bytes_sent=1_000_000, bytes_recv=2_000_000)), \
                mock.patch.object(mod.socket, "gethostname", return_value="host"), \
                mock.patch.object(mod.socket, "gethostbyname", return_value="10.0.0.5"), \
                mock.patch.object(mod.time, "sleep", return_value=None), \
                mock.patch.object(mod.psutil, "process_iter", return_value=[
                    FakeProcess(101, "alpha", 9.0, 1.2),
                    FakeProcess(202, "beta", 4.0, 8.8),
                ]):
                snapshot = mod.get_system_snapshot(1)

            self.assertIn("SYSTEM SNAPSHOT", snapshot)
            self.assertIn("alpha", snapshot)
            self.assertIn("CPU Load: 12.5%", snapshot)
            self.assertIn("Local IP: 10.0.0.5", snapshot)

    def test_city_briefing_uses_time_lookup(self):
        with mock.patch.dict(
            os.environ,
            {"JARVIS_FEATURE_CITY_BRIEFING": "1"},
            clear=False,
        ):
            mod = reload_plugin("plugins.p01_core_system")

            class FakeResponse:
                status_code = 200

                def json(self):
                    return {"hour": 14}

            with mock.patch.object(mod, "ZoneInfo", None), \
                mock.patch.object(mod._http_session, "get", return_value=FakeResponse()):
                briefing = mod.get_city_briefing("Kyiv")

            self.assertIn("Good day, Sir.", briefing)
            self.assertIn("Kyiv is currently around 14:00", briefing)


if __name__ == "__main__":
    unittest.main()
