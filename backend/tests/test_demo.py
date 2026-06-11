"""Tests for the demo device generator and its output contract."""
import asyncio

from backend.demo import DEMO_DEVICES, DemoDevice, generate_sample, run_demo_loop
from backend.scanner import DeviceStore


# ---------------------------------------------------------------------------
# generate_sample
# ---------------------------------------------------------------------------

class TestGenerateSample:
    def test_returns_float_or_none(self):
        dev = DEMO_DEVICES[0]
        for _ in range(100):
            result = generate_sample(dev)
            assert result is None or isinstance(result, float)

    def test_latency_positive_when_up(self):
        dev = DEMO_DEVICES[0]
        for _ in range(200):
            result = generate_sample(dev)
            if result is not None:
                assert result > 0

    def test_stable_device_rarely_goes_down(self):
        """Router (outage_prob=0.005) → ≥95 % uptime over 1 000 samples."""
        router = DEMO_DEVICES[0]
        results = [generate_sample(router) for _ in range(1000)]
        up_ratio = sum(r is not None for r in results) / len(results)
        assert up_ratio >= 0.95

    def test_flaky_device_produces_outages(self):
        """Thermostat (outage_prob=0.15) should have at least one None in 500 samples."""
        thermostat = DEMO_DEVICES[-1]
        results = [generate_sample(thermostat) for _ in range(500)]
        assert any(r is None for r in results)

    def test_zero_outage_prob_never_none(self):
        dev = DemoDevice("1.1.1.1", "stable", 10.0, 1.0, 0.0)
        assert all(generate_sample(dev) is not None for _ in range(300))

    def test_full_outage_prob_always_none(self):
        dev = DemoDevice("1.1.1.1", "dead", 10.0, 1.0, 1.0)
        assert all(generate_sample(dev) is None for _ in range(100))

    def test_latency_floor_at_0_1(self):
        """Even with extreme negative jitter the floor is 0.1 ms."""
        dev = DemoDevice("1.1.1.1", "jittery", 0.05, 100.0, 0.0)
        for _ in range(200):
            result = generate_sample(dev)
            assert result is not None and result >= 0.1

    def test_eight_demo_devices(self):
        assert len(DEMO_DEVICES) == 8

    def test_unique_ips(self):
        ips = [d.ip for d in DEMO_DEVICES]
        assert len(ips) == len(set(ips))

    def test_unique_hostnames(self):
        names = [d.hostname for d in DEMO_DEVICES]
        assert len(names) == len(set(names))

    def test_all_devices_have_positive_base_latency(self):
        for dev in DEMO_DEVICES:
            assert dev.base_latency > 0
            assert dev.jitter >= 0
            assert 0.0 <= dev.outage_prob <= 1.0


# ---------------------------------------------------------------------------
# Integration: one pass of the demo loop logic
# ---------------------------------------------------------------------------

def _run_one_pass() -> tuple[DeviceStore, list[dict]]:
    store = DeviceStore()
    messages: list[dict] = []

    async def mock_broadcast(msg: dict) -> None:
        messages.append(msg)

    async def one_pass() -> None:
        for dev in DEMO_DEVICES:
            latency = generate_sample(dev)
            rec, changed = store.record(dev.ip, latency, dev.hostname)
            await mock_broadcast(
                {
                    "type": "status_change" if changed else "update",
                    "device": rec.to_info().model_dump(),
                }
            )

    asyncio.run(one_pass())
    return store, messages


class TestDemoLoop:
    def test_one_pass_populates_all_eight_devices(self):
        store, _ = _run_one_pass()
        assert len(store.all_info()) == 8

    def test_one_pass_emits_one_message_per_device(self):
        _, messages = _run_one_pass()
        assert len(messages) == 8

    def test_message_type_is_valid(self):
        _, messages = _run_one_pass()
        for msg in messages:
            assert msg["type"] in ("update", "status_change")

    def test_message_device_has_required_fields(self):
        _, messages = _run_one_pass()
        for msg in messages:
            d = msg["device"]
            assert "ip" in d
            assert "status" in d
            assert "uptime_pct" in d
            assert d["status"] in ("up", "down")

    def test_hostnames_match_demo_config(self):
        store, _ = _run_one_pass()
        expected = {dev.ip: dev.hostname for dev in DEMO_DEVICES}
        for info in store.all_info():
            assert info.hostname == expected[info.ip]

    def test_first_sample_triggers_status_change(self):
        """Every device starts with no samples (status=down); first up sample is a change."""
        _, messages = _run_one_pass()
        up_messages = [m for m in messages if m["device"]["status"] == "up"]
        for m in up_messages:
            assert m["type"] == "status_change"
