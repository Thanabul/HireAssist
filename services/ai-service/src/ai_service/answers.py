"""What the model is required to return, and the arithmetic done on it here.

These models validate the provider's JSON before any of it reaches a proto
message. A malformed answer raises here and the handler turns it into a
status — it never becomes a partial score.
"""

from pydantic import BaseModel, Field


class DerivedCriterion(BaseModel):
    text: str = Field(min_length=1)
    must_have: bool
    weight: int = Field(ge=0, le=100, default=0)
    category: str = ""


class DerivedCriteria(BaseModel):
    proposed_title: str = Field(min_length=1)
    criteria: list[DerivedCriterion] = Field(min_length=1)
    uninterpreted: list[str] = []


class ExtractedJob(BaseModel):
    title: str = ""
    organisation: str = ""
    start: str = ""
    end: str = ""
    summary: str = ""


class ExtractedQualification(BaseModel):
    qualification: str = ""
    institution: str = ""
    completed: str = ""


class ExtractedProfile(BaseModel):
    """Deliberately permissive about emptiness.

    A resume with no listed skills is ordinary; a new graduate with no work
    history is ordinary. Only a profile that is empty in every field at once
    means extraction failed, and the handler decides that — not this model,
    which cannot distinguish a sparse resume from a failed one field by field.
    """

    work_history: list[ExtractedJob] = []
    skills: list[str] = []
    education: list[ExtractedQualification] = []
    additional_text: str = ""

    def is_empty(self) -> bool:
        return not (
            self.work_history or self.skills or self.education or self.additional_text.strip()
        )


class Assessment(BaseModel):
    criterion_id: str = Field(min_length=1)
    met: bool
    score: int = Field(ge=0, le=100)
    evidence: str = ""


class Scoring(BaseModel):
    assessments: list[Assessment] = Field(min_length=1)
    #: A score without a justification is not an acceptable output (UC-2), so
    #: the empty string fails validation rather than arriving at a Recruiter.
    justification: str = Field(min_length=1)


class DraftQuestion(BaseModel):
    text: str = Field(min_length=1)
    criterion_id: str = Field(min_length=1)
    source_evidence: str = ""
    kind: str = "role_depth"


class Questions(BaseModel):
    questions: list[DraftQuestion] = Field(min_length=1)


def weighted_total(assessments: list[Assessment], weights: dict[str, int]) -> int:
    """The overall score, 0-100.

    Computed here rather than asked of the model: a weighted average has a
    right answer, and a model that produces a total inconsistent with its own
    per-criterion judgements gives a Recruiter two numbers to reconcile.

    Must-have criteria carry no weight — they gate the candidate through
    ``meets_must_haves`` instead. When an opening is nothing but must-haves
    there is no weight to average, so the total falls back to the unweighted
    mean of every assessment.
    """
    weighted = [(a, weights[a.criterion_id]) for a in assessments if weights.get(a.criterion_id)]
    if weighted:
        total_weight = sum(w for _, w in weighted)
        raw = sum(a.score * w for a, w in weighted) / total_weight
    else:
        raw = sum(a.score for a in assessments) / len(assessments)
    return max(0, min(100, int(raw + 0.5)))
