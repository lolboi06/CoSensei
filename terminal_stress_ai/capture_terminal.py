from __future__ import annotations

import argparse
import json
import re
import time
from typing import List
from urllib import request, error


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str) -> dict:
    with request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _infer_suggestion_action(events: List[dict], typed_len: int) -> tuple[str, str]:
    char_keys = sum(1 for e in events if e.get("event_type") == "keydown" and isinstance(e.get("key"), str) and len(e.get("key")) == 1)
    backspaces = sum(1 for e in events if e.get("key") == "Backspace")
    pauses_700 = sum(1 for e in events if (e.get("gap_ms") or 0) > 700)
    pauses_1500 = sum(1 for e in events if (e.get("gap_ms") or 0) > 1500)
    backspace_ratio = backspaces / max(char_keys, 1)

    if typed_len < 3:
        return "none", "Very short input; no reliable suggestion signal."
    if backspace_ratio >= 0.18 or (pauses_1500 >= 1 and backspaces >= 1):
        return "override", "High correction/hesitation pattern suggests overriding AI output."
    if backspaces == 0 and pauses_700 <= 1:
        return "accept", "Fluent low-friction typing suggests accepting AI output."
    return "none", "Mixed behavior; no clear accept/override signal."


def _content_signals(text: str) -> dict:
    t = text.strip()
    if not t:
        return {
            "content_intensity": 0.0,
            "profanity_count": 0,
            "insult_count": 0,
            "exclamation_count": 0,
            "caps_ratio": 0.0,
            "distrust_intent": 0.0,
        }

    profanity_lexicon = {
        "fuck",
        "fucking",
        "shit",
        "bitch",
        "asshole",
        "bastard",
        "damn",
    }
    tokens = [w.strip(".,!?;:\"'()[]{}").lower() for w in t.split()]

    def _normalize(tok: str) -> str:
        # Collapse elongated letters: "fuckkkkk" -> "fuckk", "shiiit" -> "shiit"
        return re.sub(r"(.)\1{2,}", r"\1\1", tok)

    def _is_profanity(tok: str) -> bool:
        n = _normalize(tok)
        if n in profanity_lexicon:
            return True
        # Catch common elongated/stem variants.
        stems = ("fuck", "shit", "bitch", "asshole", "bastard", "damn")
        return any(n.startswith(stem) for stem in stems)

    profanity_count = sum(1 for tok in tokens if _is_profanity(tok))
    insult_stems = ("suck", "sck", "idiot", "stupid", "dumb", "moron", "loser", "trash")
    insult_count = sum(1 for tok in tokens if any(_normalize(tok).startswith(st) for st in insult_stems))
    exclamation_count = t.count("!")
    alpha_chars = [c for c in t if c.isalpha()]
    caps_chars = [c for c in alpha_chars if c.isupper()]
    caps_ratio = len(caps_chars) / max(len(alpha_chars), 1)

    # One profanity token should already be treated as high-intensity.
    profanity_score = min(1.0, float(profanity_count))
    insult_score = min(1.0, float(insult_count))
    exclaim_score = min(1.0, exclamation_count / 3.0)
    caps_score = min(1.0, caps_ratio / 0.5)
    content_intensity = min(1.0, 0.55 * profanity_score + 0.25 * insult_score + 0.10 * exclaim_score + 0.10 * caps_score)
    lower_t = t.lower()
    compact_t = re.sub(r"[^a-z0-9\s]", " ", lower_t)
    compact_t = re.sub(r"\s+", " ", compact_t).strip()
    tokens = compact_t.split()
    norm_tokens = [re.sub(r"(.)\1{2,}", r"\1\1", tok) for tok in tokens]
    token_text = " ".join(norm_tokens)
    distrust_intent = 0.0

    # Phrase-level matches.
    if re.search(r"\bdo\s+not\s+trust\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bcannot\s+trust\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bcant\s+trust\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bdistrust\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bunreliable\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bdo\s+not\s+believe\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bshut\s+up\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\b(you|u)\s+did\s+wrong\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\bwrong\s+answer\b", token_text):
        distrust_intent = 1.0
    if re.search(r"\byou\s+are\s+wrong\b", token_text):
        distrust_intent = 1.0

    # Token-window matches: "don t trust", "dont trust", elongated "doonnt trust".
    for i in range(len(norm_tokens) - 1):
        a = norm_tokens[i]
        b = norm_tokens[i + 1]
        if b in {"trust", "believe"}:
            if a in {"dont", "don", "cant", "cannot", "not"}:
                distrust_intent = 1.0
            # handle split forms: "don t trust", "can t trust"
            if i > 0 and norm_tokens[i - 1] in {"don", "can"} and a == "t":
                distrust_intent = 1.0

    if distrust_intent >= 1.0:
        # Ensure explicitly distrustful/disrespectful text contributes to intensity.
        content_intensity = max(content_intensity, 0.35)

    return {
        "content_intensity": round(content_intensity, 3),
        "profanity_count": int(profanity_count),
        "insult_count": int(insult_count),
        "exclamation_count": int(exclamation_count),
        "caps_ratio": round(caps_ratio, 3),
        "distrust_intent": distrust_intent,
    }


def _print_chat_response(resp: dict, suggestion: str, reason: str, show_json: bool) -> None:
    risk_scores = resp.get("risk_severity_scores", {}) or {}
    risk_value = max((float(value) for value in risk_scores.values()), default=0.0)
    if risk_value < 0.33:
        risk_level = "low"
    elif risk_value < 0.66:
        risk_level = "medium"
    else:
        risk_level = "high"

    print("\nAssistant:")
    assistant_message = str(resp.get("assistant_message", "")).strip()
    current_question = str(next(iter(resp.get("clarification_questions", [])), "")).strip()
    if assistant_message and current_question and assistant_message == current_question:
        assistant_message = ""
    if assistant_message and current_question and assistant_message.endswith(current_question):
        assistant_message = ""
    if assistant_message and current_question:
        numbered_question = f"1. {current_question}"
        if numbered_question in assistant_message:
            assistant_message = ""
    message_already_printed = False
    if assistant_message:
        print(assistant_message)
        message_already_printed = True
        if resp.get("clarification_required"):
            print()

    if resp.get("clarification_required"):
        print(current_question or "I need one more detail before I can continue.")
    elif resp.get("suggestions"):
        recommended = resp.get("suggestion", {})
        print("Here are the possible solutions:")
        for item in resp.get("suggestions", []):
            strategy = str(item.get("strategy", "option")).title()
            print(f"{item.get('id', '?')}. {strategy}")
        if recommended:
            print(f"\nRecommended solution: {recommended.get('id', '?')}")
    else:
        explanation = str(resp.get("suggestion", {}).get("explanation", "")).strip()
        content = str(resp.get("suggestion", {}).get("content", "")).strip()
        fallback_message = explanation or content or "No assistant response available."
        if not message_already_printed:
            print(fallback_message)

    print(
        "\nStatus:"
        f" trust={resp.get('trust_in_ai', {}).get('level', 'unknown')}"
        f" risk={risk_level}"
        f" mode={resp.get('shared_autonomy', {}).get('autonomy_mode', 'unknown')}"
    )

    if show_json:
        print("\n--- Structured Analysis ---")
        print(f"Inferred suggestion action: {suggestion} ({reason})")
        print(json.dumps(resp, indent=2))
        print("---------------------------")


def capture_line_events(text_prompt: str, session_id: str, api_base: str, show_json: bool = False) -> None:
    try:
        import msvcrt
    except ImportError:
        raise RuntimeError("This terminal capture script currently supports Windows (msvcrt).")

    print(text_prompt)
    print("Type your input. Press Enter to submit; ESC to finish session.")

    while True:
        events: List[dict] = []
        typed = []
        last_ts = None
        line_backspaces = 0

        while True:
            ch = msvcrt.getwch()
            now = time.perf_counter() * 1000.0
            gap = None if last_ts is None else now - last_ts
            last_ts = now

            if ch == "\x1b":
                print("\nSession ended.")
                return

            key_label = "Enter" if ch == "\r" else ("Backspace" if ch == "\x08" else ch)
            events.append(
                {
                    "ts_ms": now,
                    "event_type": "keydown",
                    "key": key_label,
                    "gap_ms": gap,
                    "suggestion_action": "none",
                }
            )

            if ch == "\r":
                print()
                break
            if ch == "\x08":
                if typed:
                    typed.pop()
                    line_backspaces += 1
                    print("\b \b", end="", flush=True)
            else:
                typed.append(ch)
                print(ch, end="", flush=True)

        typed_text = "".join(typed)
        suggestion, reason = _infer_suggestion_action(events, len(typed))
        text_signals = _content_signals(typed_text)
        if (
            text_signals["content_intensity"] >= 0.25
            or text_signals["distrust_intent"] >= 1.0
            or text_signals["insult_count"] > 0
        ):
            suggestion = "none"
            reason = "High emotional intensity or explicit distrust detected; treating suggestion decision as neutral."
        if len(typed) == 0:
            print("\nEmpty input ignored. Type some text or press ESC to exit.")
            print("Next input line (ESC to end):")
            continue
        if events:
            events[-1]["suggestion_action"] = suggestion
            events[-1]["line_text"] = typed_text
            events[-1]["backspace_count"] = line_backspaces
            events[-1].update(text_signals)

        try:
            _post_json(f"{api_base}/events", {"session_id": session_id, "events": events})
            resp = _get_json(f"{api_base}/analysis/{session_id}")
        except error.URLError as exc:
            print(f"\nServer unavailable at {api_base}. Details: {exc}")
            print("Start server first: py app\\main.py")
            print("Next input line (ESC to end):")
            continue

        _print_chat_response(resp, suggestion, reason, show_json)
        print()
        print("Next input line (ESC to end):")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="demo-session")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--show-json", action="store_true")
    args = parser.parse_args()

    capture_line_events(
        text_prompt="Terminal interaction capture is active.",
        session_id=args.session,
        api_base=args.api,
        show_json=args.show_json,
    )


if __name__ == "__main__":
    main()
