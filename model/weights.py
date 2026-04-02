SCORING_WEIGHTS = {
    "Intern": {
        "skills": 0.5,
        "experience": 0.2,
        "education": 0.3
    },
    "Fresher": {
        "skills": 0.4,
        "experience": 0.4,
        "education": 0.2
    },
    "Experienced": {
        "skills": 0.4,
        "experience": 0.5,
        "education": 0.1
    }
}

def get_scoring_weights(level: str = "Fresher") -> dict:
    level = level.strip().capitalize() 
    return SCORING_WEIGHTS.get(level, SCORING_WEIGHTS["Fresher"])

# education.py
from datetime import datetime
CURRENT_YEAR = datetime.now().year
DEGREE_SCORE = {
    "phd": 1.0,
    "doctor": 1.0,
    "master": 0.85,
    "msc": 0.85,
    "m.tech": 0.85,
    "masters": 0.85,
    "bachelor": 0.65,
    "bsc": 0.65,
    "b.tech": 0.65,
    "bachelors": 0.65,
    "diploma": 0.45
}

STATUS_MULTIPLIER = {
    "completed": 1.0,
    "pursuing": 0.9,
    "ongoing": 0.9
}

RECENCY_DECAY = [
    (3, 1.0),
    (6, 0.85),
    (10, 0.7),
    (100, 0.5)
]

def get_education_weights() -> dict:
    """
    Return all weight parameters used for education scoring.
    """
    return {
        "degree_score": DEGREE_SCORE,
        "status_multiplier": STATUS_MULTIPLIER,
        "recency_decay": RECENCY_DECAY,
        "current_year": CURRENT_YEAR
    }


