from datetime import datetime

def experience_range_score(years: float, min_y: int, max_y: int) -> float:

    if years <= 0:
        return 0.0

    if min_y == 0:
        if years <= max_y:
            return min(years / max_y, 1.0)
        return max(0.5, 1 - ((years - max_y) / (max_y + 1)))

    if min_y <= years <= max_y:
        mid = (min_y + max_y) / 2

        distance = abs(years - mid)
        max_distance = (max_y - min_y) / 2

        
        if max_distance == 0:
            return 1.0

        penalty = distance / max_distance
        bias = (years - mid) / (max_y - min_y + 1e-6)

        return 1 - (0.1 * penalty) + (0.05 * bias)

    if years < min_y:
        return max(years / min_y, 0.3)

    diff = years - max_y
    penalty = diff / (max_y + 1)

    return max(1 - penalty, 0.2)

def parse_date(date_str):
    if not date_str:
        return None

    date_str = str(date_str).lower()

    if date_str == "present":
        return datetime.now()

    try:
        return datetime.strptime(date_str[:7], "%Y-%m")
    except:
        return None


def extract_year(value):
    if not value:
        return None

    value = str(value).lower()

    if value == "present":
        return datetime.now().year

    try:
        return int(value[:4])
    except:
        return None


def recent_relevant_score(relevant_experiences: list) -> float:

    if not relevant_experiences:
        return 0.0

    relevant_experiences = sorted(
        relevant_experiences,
        key=lambda x: parse_date(x.get("end")) or datetime.min,
        reverse=True
    )

    latest = relevant_experiences[0]
    year = extract_year(latest.get("end"))

    if not year:
        return 0.3

    current_year = datetime.now().year
    years_ago = current_year - year

    if years_ago == 0:
        return 1.0
    elif years_ago == 1:
        return 0.8
    elif years_ago <= 3:
        return 0.5
    else:
        return 0.2


def calculate_gap_score(relevant_experiences: list) -> float:

    if not relevant_experiences:
        return 0.5  

    relevant_experiences = sorted(
        relevant_experiences,
        key=lambda x: parse_date(x.get("start")) or datetime.min
    )

    total_gap_months = 0

    for i in range(len(relevant_experiences) - 1):
        current = relevant_experiences[i]
        next_exp = relevant_experiences[i + 1]

        current_end = parse_date(current.get("end"))
        next_start = parse_date(next_exp.get("start"))

        if not current_end or not next_start:
            continue

        gap = (
            (next_start.year - current_end.year) * 12
            + (next_start.month - current_end.month)
        )

        if gap > 0:
            total_gap_months += gap

    gap_penalty = min(total_gap_months / 24, 1.0)
    gap_score = 1 - gap_penalty

    return gap_score


def internship_bonus_for_intern_role(internship_years: float) -> float:

    if internship_years <= 0:
        return 0.0

    score = min(internship_years / 1.0, 1.0)
    return round(0.3 * score, 4)


def final_experience_score(
    relevant_data: dict,
    job: dict,
    candidate_type: str = "Experienced"
) -> dict:

    relevant_experiences = relevant_data.get("relevant_experiences", [])
    total_years = relevant_data.get("total_relevant_years", 0.0)
    internship_years = relevant_data.get("internship_years", 0.0)

    exp = job.get("experience", {})

    try:
        min_y = max(int(exp.get("minExp", 0)), 0)
    except:
        min_y = 0

    try:
        max_y = int(exp.get("maxExp", 1))
    except:
        max_y = 1

    if max_y < min_y:
        max_y = min_y if min_y > 0 else 1

    range_score = experience_range_score(total_years, min_y, max_y)
    recency_score = recent_relevant_score(relevant_experiences)
    gap_score = calculate_gap_score(relevant_experiences)

 
    if candidate_type == "Intern":

        internship_bonus = internship_bonus_for_intern_role(internship_years)

        final = (
            0.4 * range_score
            + 0.4 * recency_score
            + internship_bonus
            + 0.2 * gap_score
        )

    elif candidate_type == "Fresher":

        internship_bonus = internship_bonus_for_intern_role(internship_years)

        final = (
            0.5 * range_score
            + 0.2 * recency_score
            + internship_bonus
            + 0.3 * gap_score
        )

    else:  

        internship_bonus = 0.0

        final = (
            0.6 * range_score
            + 0.25 * recency_score
            + 0.15 * gap_score
        )

    final = max(min(final, 1.0), 0.0)

    return {
        "score": round(final, 4),
        "details": {
            "range_score": round(range_score, 4),
            "recency_score": round(recency_score, 4),
            "gap_score": round(gap_score, 4),
            "internship_bonus": round(internship_bonus, 4),
            "internship_years": internship_years,
            "total_years": total_years,
            "candidate_type": candidate_type,
            "min_required": min_y,
            "max_allowed": max_y
        }
    }

results = []

