from __future__ import annotations

import argparse
import json
import sys

import requests
import websocket
from websocket import WebSocketBadStatusException


def build_cookie_header(session: requests.Session) -> str:
    return "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke check for authenticated realtime websocket.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    ws_base = base_url.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    ws_candidates = [
        f"{ws_base}/api/realtime",
        f"{ws_base}/api/realtime/",
        f"{ws_base}/realtime",
        f"{ws_base}/realtime/",
    ]

    session = requests.Session()
    login_response = session.post(
        f"{base_url}/api/auth/login",
        json={"username": args.username, "password": args.password},
        timeout=args.timeout,
        headers={"Origin": base_url},
    )
    login_response.raise_for_status()

    cookie_header = build_cookie_header(session)
    if not cookie_header:
        raise RuntimeError("No auth cookie returned from login.")

    last_error: Exception | None = None

    for ws_url in ws_candidates:
        try:
            ws = websocket.create_connection(
                ws_url,
                timeout=args.timeout,
                header=[f"Cookie: {cookie_header}"],
                origin=base_url,
            )
            try:
                message = ws.recv()
                payload = json.loads(message)
                if payload.get("type") != "status":
                    raise RuntimeError(f"Unexpected realtime payload type: {payload}")
                if "data" not in payload:
                    raise RuntimeError(f"Realtime payload missing data: {payload}")
                print(f"realtime_smoke=ok url={ws_url}")
                return 0
            finally:
                ws.close()
        except WebSocketBadStatusException as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            break

    raise RuntimeError(f"Realtime websocket handshake failed for all candidates. last_error={last_error}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"realtime_smoke=failed error={exc}", file=sys.stderr)
        raise
