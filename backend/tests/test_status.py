"""Tests for ping-output parsing, DeviceRecord status logic, and DeviceStore."""
from backend.scanner import DeviceRecord, DeviceStore, _parse_latency


# ---------------------------------------------------------------------------
# Ping output parsing
# ---------------------------------------------------------------------------

class TestParsePingLatency:
    def test_windows_integer_ms(self):
        assert _parse_latency("Reply from 192.168.1.1: bytes=32 time=5ms TTL=64") == 5.0

    def test_linux_decimal_ms(self):
        assert _parse_latency("64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=1.23 ms") == 1.23

    def test_windows_less_than_1ms(self):
        # "time<1ms" — regex captures the digit after the operator
        assert _parse_latency("Reply from 192.168.1.1: bytes=32 time<1ms TTL=128") == 1.0

    def test_timeout_returns_none(self):
        assert _parse_latency("Request timeout for icmp_seq 0") is None

    def test_empty_string_returns_none(self):
        assert _parse_latency("") is None

    def test_case_insensitive(self):
        assert _parse_latency("Time=10ms") == 10.0

    def test_large_latency(self):
        assert _parse_latency("time=999ms") == 999.0

    def test_fractional_linux(self):
        assert _parse_latency("time=0.456 ms") == 0.456


# ---------------------------------------------------------------------------
# DeviceRecord
# ---------------------------------------------------------------------------

def _rec(samples: list) -> DeviceRecord:
    r = DeviceRecord("10.0.0.1", "host")
    for v in samples:
        r.add_sample(v)
    return r


class TestDeviceRecord:
    def test_status_up_when_last_sample_has_latency(self):
        assert _rec([None, None, 10.0]).status == "up"

    def test_status_down_when_last_sample_is_none(self):
        assert _rec([10.0, 20.0, None]).status == "down"

    def test_status_down_with_no_samples(self):
        assert DeviceRecord("10.0.0.1").status == "down"

    def test_last_latency_is_most_recent(self):
        assert _rec([5.0, 10.0, 20.0]).last_latency_ms == 20.0

    def test_last_latency_none_when_down(self):
        assert _rec([5.0, None]).last_latency_ms is None

    def test_last_latency_none_with_no_samples(self):
        assert DeviceRecord("10.0.0.1").last_latency_ms is None

    def test_uptime_all_up(self):
        assert _rec([1.0, 2.0, 3.0]).uptime_pct == 100.0

    def test_uptime_all_down(self):
        assert _rec([None, None, None]).uptime_pct == 0.0

    def test_uptime_half(self):
        assert _rec([1.0, None, 1.0, None]).uptime_pct == 50.0

    def test_uptime_no_samples(self):
        assert DeviceRecord("10.0.0.1").uptime_pct == 0.0

    def test_sample_deque_capped_at_100(self):
        r = DeviceRecord("10.0.0.1")
        for i in range(150):
            r.add_sample(float(i))
        assert len(r._samples) == 100
        assert r.last_latency_ms == 149.0

    def test_to_info_fields(self):
        info = _rec([10.0]).to_info()
        assert info.ip == "10.0.0.1"
        assert info.hostname == "host"
        assert info.status == "up"
        assert info.last_latency_ms == 10.0
        assert info.uptime_pct == 100.0

    def test_to_history_includes_all_samples(self):
        h = _rec([1.0, 2.0, 3.0]).to_history()
        assert len(h.samples) == 3
        assert h.samples[2].latency_ms == 3.0


# ---------------------------------------------------------------------------
# DeviceStore
# ---------------------------------------------------------------------------

class TestDeviceStore:
    def test_get_or_create_same_object(self):
        store = DeviceStore()
        assert store.get_or_create("10.0.0.1") is store.get_or_create("10.0.0.1")

    def test_record_detects_down_to_up(self):
        store = DeviceStore()
        _, changed = store.record("10.0.0.1", 10.0)
        assert changed  # no-samples "down" → "up"

    def test_record_no_change_up_to_up(self):
        store = DeviceStore()
        store.record("10.0.0.1", 10.0)
        _, changed = store.record("10.0.0.1", 20.0)
        assert not changed

    def test_record_detects_up_to_down(self):
        store = DeviceStore()
        store.record("10.0.0.1", 10.0)
        _, changed = store.record("10.0.0.1", None)
        assert changed

    def test_record_no_change_down_to_down(self):
        store = DeviceStore()
        store.record("10.0.0.1", None)
        _, changed = store.record("10.0.0.1", None)
        assert not changed

    def test_all_info_returns_all_devices(self):
        store = DeviceStore()
        store.record("10.0.0.1", 5.0)
        store.record("10.0.0.2", 8.0)
        infos = store.all_info()
        assert len(infos) == 2
        assert {d.ip for d in infos} == {"10.0.0.1", "10.0.0.2"}

    def test_get_history_missing_returns_none(self):
        assert DeviceStore().get_history("99.99.99.99") is None

    def test_get_history_returns_samples(self):
        store = DeviceStore()
        store.record("10.0.0.1", 7.5)
        h = store.get_history("10.0.0.1")
        assert h is not None
        assert len(h.samples) == 1
        assert h.samples[0].latency_ms == 7.5
