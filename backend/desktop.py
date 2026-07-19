import logging
import multiprocessing
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

from main import OUTPUT_DIR, app


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


def _open_browser_when_ready(url: str) -> None:
    if os.getenv("DELIA_ERP_NO_BROWSER") == "1":
        return

    for _ in range(60):
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                webbrowser.open_new(url)
                return
        except OSError:
            time.sleep(0.25)


def _configure_logging() -> Path:
    log_path = Path(OUTPUT_DIR).parent / "delia-erp.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return log_path


def main() -> int:
    log_path = _configure_logging()

    try:
        port = _available_port()
        url = f"http://{HOST}:{port}/"
        threading.Thread(
            target=_open_browser_when_ready,
            args=(url,),
            daemon=True,
        ).start()

        print(f"DeliaERP е стартиран на {url}", flush=True)
        print(
            "Затворете този прозорец, за да спрете приложението.",
            flush=True,
        )
        uvicorn.run(
            app,
            host=HOST,
            port=port,
            access_log=False,
            log_config=None,
        )
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        logging.exception("DeliaERP failed to start")
        print("DeliaERP не може да бъде стартиран.", flush=True)
        print(f"Подробности: {log_path}", flush=True)
        if sys.stdin and sys.stdin.isatty():
            input("Натиснете Enter, за да затворите прозореца...")
        return 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
