import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import desktop


class FakeIcon:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeServer:
    def __init__(self):
        self.should_exit = False


def test_request_shutdown_stops_server_and_tray():
    icon = FakeIcon()
    server = FakeServer()
    shutdown_event = threading.Event()

    desktop._request_shutdown(icon, server, shutdown_event)

    assert server.should_exit is True
    assert shutdown_event.is_set()
    assert icon.stopped is True


def test_open_browser_when_ready_can_be_disabled(monkeypatch):
    monkeypatch.setenv("DELIA_ERP_NO_BROWSER", "1")
    monkeypatch.setattr(
        desktop.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()),
    )

    desktop._open_browser_when_ready("http://127.0.0.1:8765/", threading.Event())


def test_show_startup_error_uses_stderr_outside_windows(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(desktop.sys, "platform", "darwin")
    log_path = tmp_path / "delia-erp.log"

    desktop._show_startup_error(log_path)

    error_output = capsys.readouterr().err
    assert "DeliaERP не може да бъде стартиран." in error_output
    assert str(log_path) in error_output
