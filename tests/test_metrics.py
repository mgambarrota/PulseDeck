import json
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import api


class MetricsCompatibilityTests(unittest.TestCase):
    def test_real_snapshot_is_json_serializable(self):
        snapshot = api.get_metrics()
        json.dumps(snapshot, allow_nan=False)
        self.assertEqual(set(snapshot), {
            'timestamp', 'system', 'cpu', 'memory', 'storage', 'network', 'processes'
        })

    def test_unsupported_optional_metrics_do_not_break_snapshot(self):
        with patch.object(api.psutil, 'cpu_freq', side_effect=NotImplementedError), \
             patch.object(api.psutil, 'getloadavg', side_effect=OSError), \
             patch.object(api.psutil, 'disk_partitions', side_effect=PermissionError), \
             patch.object(api.psutil, 'disk_io_counters', return_value=None), \
             patch.object(api.psutil, 'net_io_counters', return_value=None), \
             patch.object(api.psutil, 'net_if_addrs', side_effect=PermissionError), \
             patch.object(api.psutil, 'net_if_stats', side_effect=NotImplementedError):
            snapshot = api.get_metrics()
        self.assertEqual(snapshot['cpu']['freq_current'], 'N/A')
        self.assertIsNone(snapshot['cpu']['load_1'])
        self.assertEqual(snapshot['storage']['partitions'], [])
        self.assertEqual(snapshot['network']['sent_total'], 'N/A')
        json.dumps(snapshot, allow_nan=False)

    def test_integer_address_families_are_supported(self):
        addresses = [SimpleNamespace(family=int(socket.AF_INET), address='127.0.0.1'),
                     SimpleNamespace(family=int(api.psutil.AF_LINK), address='00:11:22:33:44:55')]
        with patch.object(api.psutil, 'net_if_addrs', return_value={'test': addresses}):
            interface = api.get_metrics()['network']['interfaces'][0]
        self.assertEqual(interface['ipv4'], '127.0.0.1')
        self.assertEqual(interface['mac'], '00:11:22:33:44:55')


if __name__ == '__main__':
    unittest.main()
