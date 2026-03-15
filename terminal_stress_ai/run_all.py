from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import request
from urllib.error import URLError, HTTPError


def _is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _choose_port(preferred: int) -> int:
    if not _is_port_open(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_health(port: int, timeout_s: float = 10.0) -> bool:
    deadline = time.time() + timeout_s
    url = f"http://127.0.0.1:{port}/health"
    while time.time() < deadline:
        try:
            with request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def _get_json(url: str, timeout: float = 3.0) -> dict:
    with request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict, timeout: float = 3.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_config(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _prompt_int(label: str, lower: int, upper: int) -> int:
    while True:
        raw = input(f"{label} [{lower}-{upper}]: ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Enter a valid integer.")
            continue
        if lower <= value <= upper:
            return value
        print(f"Value must be between {lower} and {upper}.")


def _maybe_collect_survey(port: int, session: str) -> None:
    if not sys.stdin.isatty():
        return
    raw = input("Submit post-session survey now? [y/N]: ").strip().lower()
    if raw not in {"y", "yes"}:
        return

    print("NASA-TLX survey")
    nasa_tlx = {
        "mental_demand": _prompt_int("mental_demand", 0, 100),
        "physical_demand": _prompt_int("physical_demand", 0, 100),
        "temporal_demand": _prompt_int("temporal_demand", 0, 100),
        "performance": _prompt_int("performance", 0, 100),
        "effort": _prompt_int("effort", 0, 100),
        "frustration": _prompt_int("frustration", 0, 100),
    }

    print("Trust survey")
    trust = {
        "trust_ai_suggestions": _prompt_int("trust_ai_suggestions", 1, 5),
        "ai_reliable": _prompt_int("ai_reliable", 1, 5),
        "comfortable_relying_on_ai": _prompt_int("comfortable_relying_on_ai", 1, 5),
    }

    survey_resp = _post_json(
        f"http://127.0.0.1:{port}/survey/{session}",
        {"nasa_tlx": nasa_tlx, "trust": trust},
        timeout=10.0,
    )
    print("Survey saved:", json.dumps(survey_resp, indent=2))
    final_analysis = _get_json(f"http://127.0.0.1:{port}/analysis/{session}", timeout=10.0)
    validation = final_analysis.get("validation")
    if validation:
        print("Validation summary:", json.dumps(validation, indent=2))


def _print_final_debug(port: int, session: str) -> None:
    try:
        debug = _get_json(f"http://127.0.0.1:{port}/autonomy-debug/{session}", timeout=5.0)
    except Exception:
        return
    print("Autonomy debug:", json.dumps(debug, indent=2))


def run_session(
    session: str = "user1",
    port: int = 8000,
    grok_api_key: str = "",
    grok_model: str = "grok-3-mini",
    min_events_trend: int | None = None,
    min_events_indicators: int | None = None,
    require_llm: bool = False,
    no_save_key: bool = False,
    keep_session_history: bool = False,
    prompt_survey: bool = False,
    show_debug: bool = False,
) -> int:
    root = Path(__file__).resolve().parent
    config_path = root / ".terminal_stress_ai_config.json"
    config = _load_config(config_path)
    env = os.environ.copy()

    api_key = grok_api_key or env.get("GROK_API_KEY", "") or str(config.get("grok_api_key", ""))
    model = grok_model or str(config.get("grok_model", "grok-3-mini"))

    if api_key:
        env["GROK_API_KEY"] = api_key
        env["GROK_MODEL"] = model
    else:
        print("No Grok API key found. Run once with --grok-api-key to save it.")

    if min_events_trend is not None:
        env["MIN_EVENTS_FOR_TREND"] = str(max(1, min_events_trend))
    if min_events_indicators is not None:
        env["MIN_EVENTS_FOR_INDICATORS"] = str(max(1, min_events_indicators))

    if grok_api_key and not no_save_key:
        config["grok_api_key"] = grok_api_key
        config["grok_model"] = model
        _save_config(config_path, config)
        print(f"Saved Grok key config to: {config_path}")

    port = _choose_port(port)
    server_cmd = [sys.executable, str(root / "app" / "main.py"), "--port", str(port)]

    server = subprocess.Popen(
        server_cmd,
        cwd=str(root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not _wait_health(port):
            print(f"Server did not become ready on port {port}.")
            return 1

        if not keep_session_history:
            try:
                _post_json(f"http://127.0.0.1:{port}/session/{session}/reset", {})
            except Exception:
                pass

        try:
            llm_test = _get_json(f"http://127.0.0.1:{port}/llm-test")
            llm_info = llm_test.get("llm_enrichment", {})
            if not llm_info.get("used"):
                print(f"LLM test failed: {llm_info.get('reason', 'unknown error')}")
                if require_llm:
                    print("require-llm is enabled; stopping.")
                    print("Fix key and run: py run_all.py --session user1 --grok-api-key \"YOUR_REAL_KEY\"")
                    return 2
        except (URLError, HTTPError, TimeoutError) as exc:
            print(f"LLM test unavailable: {exc}")
            if require_llm:
                return 2
        except Exception as exc:
            print(f"LLM test error: {exc}")
            if require_llm:
                return 2

        print(f"Server started: http://127.0.0.1:{port} (PID={server.pid})")
        print("LLM mode: enabled (fallback if unavailable).")
        print("Press ESC in the client to end session.")

        client_cmd = [
            sys.executable,
            str(root / "capture_terminal.py"),
            "--session",
            session,
            "--api",
            f"http://127.0.0.1:{port}",
        ]
        exit_code = subprocess.call(client_cmd, cwd=str(root), env=env)
        if show_debug:
            _print_final_debug(port, session)
        if prompt_survey:
            try:
                _maybe_collect_survey(port, session)
            except Exception as exc:
                print(f"Survey step failed: {exc}")
        return exit_code
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
        print("Server stopped.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="user1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--grok-api-key", default="")
    parser.add_argument("--grok-model", default="grok-3-mini")
    parser.add_argument("--min-events-trend", type=int, default=None)
    parser.add_argument("--min-events-indicators", type=int, default=None)
    parser.add_argument("--require-llm", action="store_true")
    parser.add_argument("--no-save-key", action="store_true")
    parser.add_argument("--keep-session-history", action="store_true")
    parser.add_argument("--prompt-survey", action="store_true")
    parser.add_argument("--show-debug", action="store_true")
    args = parser.parse_args()

    return run_session(
        session=args.session,
        port=args.port,
        grok_api_key=args.grok_api_key,
        grok_model=args.grok_model,
        min_events_trend=args.min_events_trend,
        min_events_indicators=args.min_events_indicators,
        require_llm=args.require_llm,
        no_save_key=args.no_save_key,
        keep_session_history=args.keep_session_history,
        prompt_survey=args.prompt_survey,
        show_debug=args.show_debug,
    )


if __name__ == "__main__":
    raise SystemExit(main())
