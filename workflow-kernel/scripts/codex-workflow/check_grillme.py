#!/usr/bin/env python3
"""Check native Grill-me calls and cited answers in a real Codex session log."""

import argparse
import json
from pathlib import Path


QUESTION_TOOLS = {"request_user_input_async", "request_user_input"}


def tool_name(payload):
    return payload.get("name", "").split(".")[-1].split("__")[-1]


def message_text(payload):
    return "\n".join(
        part.get("text", "")
        for part in payload.get("content", [])
        if isinstance(part, dict)
    )


def select_turn(records, turn_id=None):
    starts = [
        (i, record.get("payload", {}).get("turn_id"))
        for i, record in enumerate(records)
        if record.get("type") == "event_msg"
        and record.get("payload", {}).get("type") == "task_started"
    ]
    matches = [item for item in starts if turn_id is None or item[1] == turn_id]
    if not matches:
        raise ValueError("当前日志中缺少指定回合的 task_started 记录")
    start, selected = matches[-1]
    end = next((i for i, _ in starts if i > start), len(records))
    return selected, list(enumerate(records[start:end], start + 1))


def check(records, turn_id=None, explanation="", answers=()):
    selected, events = select_turn(records, turn_id)
    calls = [
        (line, record["payload"])
        for line, record in events
        if record.get("type") == "response_item"
        and record.get("payload", {}).get("type") in {"function_call", "custom_tool_call"}
        and tool_name(record["payload"]) in QUESTION_TOOLS
    ]
    result = {"turn_id": selected, "native_question_calls": len(calls)}
    if not calls:
        if explanation.strip():
            return 0, dict(result, status="ready_by_explanation", explanation=explanation.strip())
        return 1, dict(result, status="explanation_required", next_action="说明本轮沿用的决定及出处，或执行原生 Grill-me")

    evidence = []
    for position, (line, call) in enumerate(calls):
        end = calls[position + 1][0] if position + 1 < len(calls) else float("inf")
        following = [(i, r["payload"]) for i, r in events if line < i < end and r.get("type") == "response_item"]
        user_messages = [(i, message_text(p)) for i, p in following if p.get("type") == "message" and p.get("role") == "user"]
        if tool_name(call) == "request_user_input":
            user_messages.extend(
                (i, p.get("output", ""))
                for i, p in following
                if p.get("type") == "function_call_output" and p.get("call_id") == call.get("call_id")
            )
        matched = [
            i for i, text in user_messages
            if any(answer.strip() and answer in text for answer in answers)
        ]
        waits = [
            i for i, p in following
            if p.get("type") in {"function_call", "custom_tool_call"} and tool_name(p) == "sleep"
        ]
        evidence.append({"question_line": line, "answer_lines": matched, "wait_lines": waits})
        if not matched:
            return 2, dict(result, status="waiting_for_answer_evidence", rounds=evidence, next_action="保持当前回合实际 wait；收到实际答案后引用原文运行校验")
    return 0, dict(result, status="ready_for_review", rounds=evidence)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, help="本聊天真实 Codex JSONL 日志")
    parser.add_argument("--turn-id", help="默认选择日志的最新回合")
    parser.add_argument("--answer", action="append", default=[], help="本轮实际用户回答的原文片段，可重复")
    parser.add_argument("--explanation", default="", help="卡片记录缺项时向用户交代的具体理由及决定出处")
    args = parser.parse_args(argv)
    try:
        if args.session is None:
            raise ValueError("本次调用需要真实会话日志来源，或具体解释")
        records = [json.loads(line) for line in args.session.read_text().splitlines() if line.strip()]
        code, result = check(records, args.turn_id, args.explanation, args.answer)
    except (OSError, ValueError) as error:
        result = {"status": "explanation_required", "evidence_issue": str(error)}
        code = 1
        if args.explanation.strip():
            code = 0
            result.update(status="ready_by_explanation", explanation=args.explanation.strip())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
