import importlib.util
from pathlib import Path
import unittest


PATH = Path(__file__).resolve().parents[1] / "workflow-kernel/scripts/codex-workflow/check_grillme.py"
SPEC = importlib.util.spec_from_file_location("check_grillme", PATH)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def item(kind, **payload):
    return {"type": kind, "payload": payload}


START = item("event_msg", type="task_started", turn_id="current")
QUESTION = item("response_item", type="function_call", name="functions.request_user_input_async", call_id="q")


class GrillmeCheckTests(unittest.TestCase):
    def test_claiming_a_card_in_text_still_requires_explanation(self):
        records = [START, item("response_item", type="message", role="assistant", content=[{"text": "Grill-me 卡片已发出 request_user_input_async"}])]
        code, result = CHECKER.check(records)
        self.assertEqual(code, 1)
        self.assertEqual(result["native_question_calls"], 0)

    def test_missing_card_accepts_an_explicit_explanation_for_review(self):
        code, result = CHECKER.check([START], explanation="用户本轮已明确要求完整正文进 AGENTS，直接沿用该决定。")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ready_by_explanation")

    def test_pending_question_keeps_waiting_even_with_an_explanation(self):
        code, result = CHECKER.check([START, QUESTION], explanation="已发送。")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "waiting_for_answer_evidence")

    def test_status_request_is_not_automatically_an_answer(self):
        records = [START, QUESTION, item("response_item", type="message", role="user", content=[{"text": "第二轮卡片呢"}])]
        code, result = CHECKER.check(records)
        self.assertEqual(code, 2)

    def test_cited_real_answer_is_ready_for_semantic_review(self):
        records = [START, QUESTION, item("response_item", type="function_call", name="clock.sleep"), item("response_item", type="message", role="user", content=[{"text": "验收到生成成功"}])]
        code, result = CHECKER.check(records, answers=["验收到生成成功"])
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ready_for_review")
        self.assertEqual(result["rounds"][0]["wait_lines"], [3])

    def test_next_round_requires_its_own_answer_evidence(self):
        records = [START, QUESTION, item("response_item", type="message", role="user", content=[{"text": "验收到生成成功"}]), QUESTION]
        code, result = CHECKER.check(records, answers=["验收到生成成功"])
        self.assertEqual(code, 2)
        self.assertEqual(len(result["rounds"]), 2)


if __name__ == "__main__":
    unittest.main()
