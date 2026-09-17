import unittest
from unittest.mock import patch

from rhos_ls_mcps import osc, settings


class MetricStorageErrorTests(unittest.TestCase):
    def test_returns_none_for_unrelated_error(self):
        self.assertIsNone(osc._metric_storage_error("some unrelated failure"))

    def test_detects_prometheus_client_failure(self):
        stderr = (
            "ERROR Failed to configure Prometheus client. Aetos discovery from "
            "keystone failed: 'public endpoint for metric-storage service ...'"
        )
        message = osc._metric_storage_error(stderr)
        self.assertIsNotNone(message)
        self.assertIn("metric-storage", message)
        self.assertIn("openstack.prometheus", message)

    def test_detects_metric_storage_mention(self):
        self.assertIsNotNone(
            osc._metric_storage_error("public endpoint for metric-storage not found")
        )


class ConfigurePrometheusEnvTests(unittest.TestCase):
    def _configure(self, prometheus, environ):
        config = settings.Settings(openstack={"prometheus": prometheus})
        with patch.object(settings, "CONFIG", config), patch.dict(
            osc.os.environ, environ, clear=True
        ):
            osc._configure_prometheus_env()
            return dict(osc.os.environ)

    def test_exports_config_values(self):
        env = self._configure(
            {"host": "h", "port": 9090, "ca_cert": "/ca", "root_path": "/p"}, {}
        )
        self.assertEqual(env["PROMETHEUS_HOST"], "h")
        self.assertEqual(env["PROMETHEUS_PORT"], "9090")
        self.assertEqual(env["PROMETHEUS_CA_CERT"], "/ca")
        self.assertEqual(env["PROMETHEUS_ROOT_PATH"], "/p")

    def test_existing_env_is_not_overridden(self):
        env = self._configure({"host": "cfg"}, {"PROMETHEUS_HOST": "preexisting"})
        self.assertEqual(env["PROMETHEUS_HOST"], "preexisting")

    def test_unset_values_are_absent(self):
        env = self._configure({"host": "h"}, {})
        self.assertNotIn("PROMETHEUS_PORT", env)
        self.assertNotIn("PROMETHEUS_ROOT_PATH", env)


if __name__ == "__main__":
    unittest.main()
