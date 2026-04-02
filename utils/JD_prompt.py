from typing import List

def jd_structuring_prompt(
    jd_paragraph: str,
    experience_input: str,
    explicit_skills_mustHave: List[str],
    explicit_skills_goodToHave: List[str],
    explicit_certifications: List[str]
) -> str:

    must_have = ", ".join(explicit_skills_mustHave or [])
    good_to_have = ", ".join(explicit_skills_goodToHave or [])
    certs = ", ".join(explicit_certifications or [])

    return f"""
You structure job descriptions for ATS candidate evaluation.
Extract structured data from JD.

STEP 1 — ROLE
Identify primary role (e.g., backend developer, data analyst, product manager). Use it to prioritize skills.

STEP 2 — SKILLS
Extract all technical/domain skills (languages, frameworks, tools, platforms, db, cloud, devops, analytics, design, standards, domain expertise).
Never return empty if tech exists.

CLASSIFY
mustHave: 4–8 core skills
goodToHave: supporting skills

NORMALIZATION
- lowercase, fix spelling, remove duplicates, trim spaces
- ≤4 words
- aliases: nodejs→node.js, reactjs→react, postgres→postgresql, ml→machine learning, nlp→natural language processing

DUPLICATES
If in both → keep only in mustHave

EXCLUDE
soft skills (team player, communication, etc.)

EXPLICIT RULE
mustHave = explicit_mustHave + extracted
goodToHave = explicit_goodToHave + extracted
Do NOT move/remove explicit skills

CANONICALIZATION
structured query language→sql
amazon web services→aws
javascript object notation→json
representational state transfer→rest

HR PRIORITY
User skills stay in same category, only normalize

STEP 3 — EXPERIENCE
Detect: 3-5, 5+, min 3, fresher, entry

RULES
- single → max=min+1
- X+ → max=min+2
- X-Y → min=X, max=Y

experienceText (4–6 sentences): include skills, tools, work, domain, collaboration
experienceTextForEmbedding (2–3 sentences): resume-style practical work

STEP 4 — CERTIFICATIONS
Include: aws, pmp, cka, rac, cfa, six sigma, google analytics
Exclude degrees, courses 

====================================================
INPUT
====================================================

JD Paragraph:
\"\"\"{jd_paragraph}\"\"\"

Experience Input:
\"\"\"{experience_input or ""}\"\"\"

Explicit Must Have:
{must_have}

Explicit Good To Have:
{good_to_have}

Explicit Certifications:
{certs}

====================================================
OUTPUT (VALID JSON ONLY)
====================================================

{{
  "skills": {{
    "mustHave": [],
    "goodToHave": []
  }},
  "experience": {{
    "experienceText": "",
    "minExp": 0,
    "maxExp": 0
  }},
  "certifications": []
}}

Return valid JSON only.
"""