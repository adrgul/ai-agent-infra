"""
Simple evaluation script for RAG pipeline.

Why this module exists:
- Provides basic evaluation of RAG answer quality
- Uses keyword-based heuristic scoring (simple but effective)
- Demonstrates eval workflow that can be extended

Design decisions:
- Keyword-based scoring (simple, deterministic)
- "I don't know" is acceptable when expected_keywords is empty
- Can be run standalone or integrated into CI

Usage:
    python -m app.eval.run_eval
"""

import sys
from typing import List, Dict, Any

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.rag.chain import answer_question, create_chat_llm
from app.rag.embeddings import create_embeddings

setup_logging()
logger = get_logger(__name__)


# Evaluation examples
# Why these examples: Cover different types of questions and expected behaviors
EVAL_EXAMPLES = [
    {
        "question": "What is the project about?",
        "expected_keywords": ["rag", "chatbot", "faiss", "streamlit", "fastapi"],
        "description": "High-level project description",
    },
    {
        "question": "How do I run the backend?",
        "expected_keywords": ["uvicorn", "app.main:app", "port", "8000"],
        "description": "Backend setup instructions",
    },
    {
        "question": "What API endpoints are available?",
        "expected_keywords": ["health", "ingest", "chat", "endpoint"],
        "description": "API endpoint documentation",
    },
    {
        "question": "How do I test the application?",
        "expected_keywords": ["pytest", "test"],
        "description": "Testing instructions",
    },
    {
        "question": "What is the capital of Mars?",
        "expected_keywords": [],  # Empty = expect "I don't know"
        "description": "Out-of-domain question (should say 'I don't know')",
    },
]


def evaluate_answer(
    answer: str,
    expected_keywords: List[str],
) -> Dict[str, Any]:
    """
    Evaluate answer using keyword-based heuristic.

    Why this function: Provides simple, deterministic evaluation
    without requiring another LLM call (LLM-as-judge is more expensive).

    Why keyword matching: Simple but effective for factual questions.
    If answer contains expected keywords, it's likely correct.

    Why case-insensitive: Variations in capitalization shouldn't affect score.

    Args:
        answer: Generated answer from RAG pipeline
        expected_keywords: Keywords that should appear in a correct answer
                          (empty list means "I don't know" is acceptable)

    Returns:
        Dict with score, passed flag, and details
    """
    # Assert: answer must not be empty
    assert answer.strip(), "Answer must not be empty"

    answer_lower = answer.lower()

    # Special case: out-of-domain questions (no expected keywords)
    # Why special handling: RAG should admit when it doesn't know
    if not expected_keywords:
        # Check if answer contains "don't know" or similar phrases
        dont_know_phrases = [
            "don't know",
            "do not know",
            "not in the",
            "cannot answer",
            "no information",
        ]

        found_dont_know = any(phrase in answer_lower for phrase in dont_know_phrases)

        return {
            "score": 1.0 if found_dont_know else 0.0,
            "passed": found_dont_know,
            "found_keywords": [],
            "missing_keywords": [],
            "reason": "Correctly says 'don't know'" if found_dont_know else "Should say 'don't know'",
        }

    # Count how many expected keywords appear in answer
    # Why set: Each keyword only counts once (even if repeated)
    found_keywords = []
    missing_keywords = []

    for keyword in expected_keywords:
        if keyword.lower() in answer_lower:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    # Score as ratio of found keywords
    # Why ratio: Simple scoring metric (0.0 to 1.0)
    score = len(found_keywords) / len(expected_keywords) if expected_keywords else 0.0

    # Pass if at least 50% of keywords found
    # Why 50%: Lenient threshold (answer doesn't need ALL keywords to be useful)
    passed = score >= 0.5

    return {
        "score": score,
        "passed": passed,
        "found_keywords": found_keywords,
        "missing_keywords": missing_keywords,
        "reason": f"Found {len(found_keywords)}/{len(expected_keywords)} keywords",
    }


def run_evaluation():
    """
    Run evaluation on all examples.

    Why this function: Main entry point for evaluation script.
    Runs all examples, scores them, and reports results.

    Returns:
        int: Exit code (0 if all passed, 1 if any failed)
    """
    # Assert: Must have eval examples
    assert len(EVAL_EXAMPLES) > 0, "Must have eval examples"

    logger.info("=" * 80)
    logger.info("Starting RAG Pipeline Evaluation")
    logger.info("=" * 80)

    settings = get_settings()
    embeddings = create_embeddings(settings)
    llm = create_chat_llm(settings)

    results = []
    passed_count = 0
    failed_count = 0

    for i, example in enumerate(EVAL_EXAMPLES, 1):
        logger.info(f"\n[{i}/{len(EVAL_EXAMPLES)}] {example['description']}")
        logger.info(f"Question: {example['question']}")

        try:
            # Generate answer using RAG pipeline
            # Why top_k=4, temperature=0.2: Default settings for consistency
            answer, sources = answer_question(
                query=example["question"],
                top_k=4,
                temperature=0.2,
                settings=settings,
                embeddings=embeddings,
                llm=llm,
            )

            logger.info(f"Answer: {answer[:200]}...")

            # Evaluate answer
            eval_result = evaluate_answer(answer, example["expected_keywords"])

            result = {
                "example": example,
                "answer": answer,
                "sources": sources,
                "eval": eval_result,
            }
            results.append(result)

            # Log evaluation result
            if eval_result["passed"]:
                logger.info(f"✅ PASSED (score: {eval_result['score']:.2f})")
                logger.info(f"   Reason: {eval_result['reason']}")
                passed_count += 1
            else:
                logger.warning(f"❌ FAILED (score: {eval_result['score']:.2f})")
                logger.warning(f"   Reason: {eval_result['reason']}")
                if eval_result["missing_keywords"]:
                    logger.warning(f"   Missing keywords: {eval_result['missing_keywords']}")
                failed_count += 1

        except Exception as e:
            logger.error(f"❌ ERROR: {e}", exc_info=True)
            failed_count += 1
            results.append({
                "example": example,
                "error": str(e),
                "eval": {"passed": False, "score": 0.0},
            })

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Evaluation Summary")
    logger.info("=" * 80)
    logger.info(f"Total examples: {len(EVAL_EXAMPLES)}")
    logger.info(f"Passed: {passed_count}")
    logger.info(f"Failed: {failed_count}")

    avg_score = sum(r["eval"]["score"] for r in results if "eval" in r) / len(results)
    logger.info(f"Average score: {avg_score:.2f}")

    # Return exit code
    # Why exit code: Allows CI to detect evaluation failures
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    """
    Main entry point when run as script.

    Why __main__: Allows running as: python -m app.eval.run_eval
    """
    exit_code = run_evaluation()
    sys.exit(exit_code)
