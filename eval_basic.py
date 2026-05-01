#!/usr/bin/env python
"""Small evaluation harness for the current RAG implementation."""

from src import generation


TEST_SET = [
    "What does this HR manual say about annual holidays?",
    "What is mentioned about employee exit process?",
    "Are there references to employee death notification process?",
]


def run_eval() -> int:
    passed = 0

    for idx, question in enumerate(TEST_SET, start=1):
        result = generation.answer_question(question=question, top_k=5)
        answer = result["answer"].strip()
        contexts = result["contexts"]

        ok = bool(answer) and len(contexts) > 0
        status = "PASS" if ok else "FAIL"
        print(f"[{idx}] {status} | {question}")

        if ok:
            passed += 1

    total = len(TEST_SET)
    print(f"\nScore: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run_eval())
