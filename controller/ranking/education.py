import re
from typing import List, Dict, Union
from model.weights import get_education_weights
from services.app_error import AppError

try:
    WEIGHTS = get_education_weights()
except Exception as e:
    raise AppError(f"Failed to load education weights: {str(e)}", 500)

DEGREE_SCORE = WEIGHTS["degree_score"]
STATUS_MULTIPLIER = WEIGHTS["status_multiplier"]
RECENCY_DECAY = WEIGHTS["recency_decay"]
CURRENT_YEAR = WEIGHTS["current_year"]

class CandidateType:
    INTERN = "Intern"
    FRESHER = "Fresher"
    EXPERIENCED = "Experienced"


def normalize_degree(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"[.\-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_degree_score(level_text: str) -> Union[float, None]:
    if not isinstance(level_text, str):
        return None

    text = normalize_degree(level_text)

    for key, score in sorted(DEGREE_SCORE.items(), key=lambda x: len(x[0]), reverse=True):
        if normalize_degree(key) in text:
            return score

    return None


def extract_year(value: Union[str, int, None]) -> Union[int, None]:
    if not value:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        match = re.search(r"\b(19|20)\d{2}\b", value)
        if match:
            return int(match.group())

    return None


def recency_factor(end_value: Union[str, int, None]) -> float:
    year = extract_year(end_value)
    if not year:
        return 1.0

    years_ago = CURRENT_YEAR - year

    for max_years, factor in RECENCY_DECAY:
        if years_ago <= max_years:
            return factor

    return 0.5

def intern_priority_factor(end_value: Union[str, int, None], status: str = "", level: str = "") -> float:
    year = extract_year(end_value)
    level = (level or "").lower()
    status = (status or "").lower()

    if not year:
        return 0.65

    diff = year - CURRENT_YEAR  


    if diff == 0:
        base = 1.15   
    elif diff == 1:
        base = 1.1
    elif diff == 2:
        base = 0.85   
    elif diff >= 3:
        base = 0.7
    else:
        years_ago = abs(diff)
        if years_ago == 1:
            base = 1.0   
        elif years_ago == 2:
            base = 0.85
        else:
            base = 0.75

    
    if status == "pursuing":
        base += 0.05
    elif status == "completed":
        base -= 0.02


    if "master" in level and status == "pursuing" and diff <= 1:
        base += 0.08

    if status == "pursuing" and diff >= 2:
        base -= 0.15

    if "master" in level and status == "completed" and diff >= -1:
        base += 0.04

    base = max(0.5, min(base, 1.0))

    return round(base, 4)

def _build_intern_reason(level: str, status: str, end_value) -> str:
    year = extract_year(end_value)
    year_str = f" ({year})" if year else ""

    if status == "completed":
        return f"Graduated {level}{year_str}"

    if status == "pursuing":
        return f"Pursuing {level}{year_str}"

    return f"{status.title()} {level}{year_str}"


def _build_general_reason(level: str, status: str, end_value) -> str:
    year = extract_year(end_value)
    year_str = f" ({year})" if year else ""

    if status == "completed":
        return f"Completed {level}{year_str}"

    return f"{status.title()} {level}{year_str}"


def education_score(
    resume_education: List[Dict],
    candidate_type: str = CandidateType.FRESHER
) -> dict:

    candidate_type = str(candidate_type).lower().strip()

    if not isinstance(resume_education, list):
        return {
            "score": 0.0,
            "details": "Invalid education format"
        }

    best_score = 0.0
    best_reason = "No qualifying education"

    for edu in resume_education:
        if not isinstance(edu, dict):
            continue

        level = edu.get("level", "")
        status = str(edu.get("status", "")).lower()
        end_value = edu.get("end")

        detected = detect_degree_score(level)
        base = detected if detected is not None else 0.4

        level_lower = level.lower()


        if candidate_type == CandidateType.INTERN:

            priority_mult = intern_priority_factor(end_value, status=status, level=level)
            score = round(base * priority_mult, 4)

            if score > best_score:
                best_score = score
                best_reason = _build_intern_reason(level, status, end_value)

      
        else:

            status_mult = STATUS_MULTIPLIER.get(status, 0.8)
            score = base * status_mult

            if status == "completed":
                score += 0.05 * recency_factor(end_value)

            if "master" in level_lower and status == "pursuing":
                score = max(score, 0.85 * base)

            if "bachelor" in level_lower and status == "completed":
                score = min(score, base * 1.0)

            score = round(score, 4)

            if score > best_score:
                best_score = score
                best_reason = _build_general_reason(level, status, end_value)

    return {
        "score": round(best_score, 4),
        "details": best_reason
    }

