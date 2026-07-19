import logging
import multiprocessing
import os
import socket
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

import pystray
import uvicorn
from PIL import Image

from main import OUTPUT_DIR, WEB_DIR, app


HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PORT_ATTEMPTS = 20


def _available_port() -> int:
    configured_port = os.getenv("DELIA_ERP_PORT")
    ports = [int(configured_port)] if configured_port else range(
        DEFAULT_PORT,
        DEFAULT_PORT + PORT_ATTEMPTS,
    )

    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return port

    raise RuntimeError("Няма свободен локален порт за стартиране на DeliaERP.")


def _open_browser(url: str) -> None:
    try:
        webbrowser.open_new(url)
    except Exception:
        logging.exception("Could not open DeliaERP in the default browser")


def _open_browser_when_ready(url: str, shutdown_event: threading.Event) -> None:
    if os.getenv("DELIA_ERP_NO_BROWSER") == "1":
        return

    for _ in range(60):
        if shutdown_event.is_set():
            return
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                _open_browser(url)
                return
        except OSError:
            shutdown_event.wait(0.25)


def _tray_image() -> Image.Image:
    icon_path = WEB_DIR / "favicon.ico"
    try:
        with Image.open(icon_path) as image:
            return image.convert("RGBA")
    except OSError:
        logging.warning("Could not load tray icon from %s", icon_path, exc_info=True)
        return Image.new("RGBA", (64, 64), "#006b5f")


def _request_shutdown(
    icon: pystray.Icon,
    server: uvicorn.Server,
    shutdown_event: threading.Event,
) -> None:
    logging.info("DeliaERP shutdown requested from the tray")
    shutdown_event.set()
    server.should_exit = True
    icon.stop()


def _run_with_tray(server: uvicorn.Server, url: str) -> None:
    shutdown_event = threading.Event()
    server_errors: list[Exception] = []

    icon: pystray.Icon

    def run_server() -> None:
        try:
            server.run()
        except Exception as exc:
            server_errors.append(exc)
        finally:
            shutdown_event.set()
            icon.stop()

    server_thread = threading.Thread(
        target=run_server,
        name="delia-erp-server",
        daemon=True,
    )

    def setup_tray(tray_icon: pystray.Icon) -> None:
        tray_icon.visible = True
        server_thread.start()
        threading.Thread(
            target=_open_browser_when_ready,
            args=(url, shutdown_event),
            name="delia-erp-browser",
            daemon=True,
        ).start()

    icon = pystray.Icon(
        "DeliaERP",
        _tray_image(),
        "DeliaERP",
        menu=pystray.Menu(
            pystray.MenuItem(
                "Отвори DeliaERP",
                lambda _icon, _item: _open_browser(url),
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Изход",
                lambda tray_icon, _item: _request_shutdown(
                    tray_icon,
                    server,
                    shutdown_event,
                ),
            ),
        ),
    )

    try:
        icon.run(setup=setup_tray)
    finally:
        shutdown_event.set()
        server.should_exit = True
        if server_thread.ident is not None:
            server_thread.join(timeout=10)

    if server_errors:
        raise server_errors[0]
    if server_thread.is_alive():
        raise RuntimeError("DeliaERP server did not stop cleanly.")
    if not server.started:
        raise RuntimeError("DeliaERP server did not start successfully.")


def _configure_logging() -> Path:
    log_path = Path(OUTPUT_DIR).parent / "delia-erp.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    return log_path


def _show_startup_error(log_path: Path) -> None:
    message = (
        "DeliaERP не може да бъде стартиран.\n\n"
        f"Подробности: {log_path}"
    )
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "DeliaERP", 0x10)
            return
        except Exception:
            logging.exception("Could not display the DeliaERP error dialog")

    if sys.stderr is not None:
        print(message, file=sys.stderr, flush=True)


def main() -> int:
    log_path = _configure_logging()

    try:
        port = _available_port()
        url = f"http://{HOST}:{port}/"
        logging.info("Starting DeliaERP at %s", url)
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host=HOST,
                port=port,
                access_log=False,
                log_config=None,
            )
        )
        _run_with_tray(server, url)
        logging.info("DeliaERP stopped")
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        logging.exception("DeliaERP failed to start")
        _show_startup_error(log_path)
        return 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
