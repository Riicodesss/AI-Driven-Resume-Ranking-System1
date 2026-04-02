from typing import Dict

JD_SKILL_WEIGHTS = {
    "must_have": 0.7,
    "good_to_have": 0.3
}

def final_skill_score_from_counts(
    matched_must_have: int,
    matched_good_to_have: int,
    total_must_have: int,
    total_good_to_have: int
) -> Dict:
    """
    Compute final weighted skill score based on JD skill coverage.
    """

    must_score = (
        matched_must_have / total_must_have
        if total_must_have > 0 else 1.0
    )

    good_score = (
        matched_good_to_have / total_good_to_have
        if total_good_to_have > 0 else 0.0
    )

    final_score = (
        must_score * JD_SKILL_WEIGHTS["must_have"] +
        good_score * JD_SKILL_WEIGHTS["good_to_have"]
    )

    return {
        "must_have_score": round(must_score, 4),
        "good_to_have_score": round(good_score, 4),
        "final_skill_score": round(final_score, 4)
    }