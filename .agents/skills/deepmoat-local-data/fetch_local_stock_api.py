from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
OUTPUTS_DIR = ROOT / "outputs"
DEFAULT_BASE_URL = "http://localhost:5100"
DEFAULT_ROUTE_TEMPLATE = "/stock/{ts_code}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a local stock API response and save it under outputs/."
    )
    parser.add_argument("--ts-code", help="Stock code such as 000592.SZ.")
    parser.add_argument("--url", help="Full local API URL. Overrides --ts-code.")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL used with --ts-code. Default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--route-template",
        default=DEFAULT_ROUTE_TEMPLATE,
        help=f"Path template used with --ts-code. Default: {DEFAULT_ROUTE_TEMPLATE}",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. Default is derived from ts_code or URL.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds. Default: 10.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved URL and output path without sending a request.",
    )
    args = parser.parse_args()

    if not args.url and not args.ts_code:
        parser.error("either --url or --ts-code is required")
    return args


def build_url(args: argparse.Namespace) -> str:
    if args.url:
        return args.url
    route = args.route_template.format(ts_code=args.ts_code)
    return f"{args.base_url.rstrip('/')}{route}"


def default_output_path(url: str, ts_code: str | None, explicit_output: str | None) -> Path:
    if explicit_output:
        return Path(explicit_output).expanduser().resolve()

    OUTPUTS_DIR.mkdir(exist_ok=True)
    if ts_code:
        filename = f"stock-{ts_code.replace('.', '-')}.json"
        return OUTPUTS_DIR / filename

    stem = url.replace("http://", "").replace("https://", "").replace("/", "-")
    return OUTPUTS_DIR / f"{stem}.json"


def decode_body(raw: bytes) -> tuple[object, bool]:
    text = raw.decode("utf-8")
    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        return text, False


def fetch(url: str, timeout: float) -> tuple[object, bool]:
    request = Request(url, headers={"Accept": "application/json, text/plain;q=0.9, */*;q=0.8"})
    with urlopen(request, timeout=timeout) as response:
        return decode_body(response.read())


def validate_payload(payload: object) -> None:
    if isinstance(payload, dict) and "code" in payload and payload["code"] != 200:
        message = payload.get("message", "unknown error")
        raise ValueError(f"local API returned code={payload['code']}: {message}")


def save_payload(path: Path, payload: object, is_json: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if is_json:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    path.write_text(str(payload), encoding="utf-8")


def main() -> int:
    args = parse_args()
    url = build_url(args)
    output_path = default_output_path(url, args.ts_code, args.output)

    print(f"URL: {url}")
    print(f"Output: {output_path}")

    if args.dry_run:
        print("Dry run only; request skipped.")
        return 0

    try:
        payload, is_json = fetch(url, args.timeout)
        validate_payload(payload)
        save_payload(output_path, payload, is_json)
    except HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Connection error: {exc.reason}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Saved payload to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
