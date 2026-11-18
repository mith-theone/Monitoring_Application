"""Local demo entrypoint — run with: python app.py"""

import os
import socket

from app import create_app
from app.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME

app = create_app()


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    # Prefer 5303 — on shared lab hosts port 5000 is often another student's app.
    preferred = int(os.environ.get("PORT", "5303"))
    port = preferred
    if not _port_free(port):
        for candidate in (5303, 5304, 5305, 5000):
            if _port_free(candidate):
                port = candidate
                break
        else:
            raise SystemExit("No free port found. Set PORT=....")

    user = app.config.get("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    print(f"This is jumpuser3 Demo Monitoring")
    print(f"Demo login: {user} / {DEFAULT_ADMIN_PASSWORD}")
    print(f"Open http://127.0.0.1:{port}/login")
    if port == 5000:
        print("WARNING: port 5000 is crowded on shared hosts — prefer 5303")
    app.run(host=host, port=port, debug=False)
