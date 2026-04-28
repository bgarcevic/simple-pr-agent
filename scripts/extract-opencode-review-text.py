import json
import pathlib
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract-opencode-review-text.py <input> <output>", file=sys.stderr)
        return 1

    raw_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2])

    raw = raw_path.read_text(errors="replace")
    raw = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw)
    raw = raw.replace("\r", "").strip()

    last_text = None
    final_text = None

    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") != "text":
            continue

        part = event.get("part") or {}
        text = part.get("text")
        if not text:
            continue

        last_text = text

        metadata = part.get("metadata") or {}
        openai = metadata.get("openai") or {}
        if openai.get("phase") == "final_answer":
            final_text = text

    chosen_text = final_text or last_text
    if chosen_text:
        body = "## Duo PR AI Review\n\n" + chosen_text.rstrip()
    else:
        fallback = raw[:60000] + "\n\n[output truncated]" if len(raw) > 60000 else raw
        body = "## Duo PR AI Review\n\n```json\n" + fallback + "\n```"

    payload = {
        "comments": [
            {
                "parentCommentId": 0,
                "content": body,
                "commentType": 1,
            }
        ],
        "status": 1,
    }
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
