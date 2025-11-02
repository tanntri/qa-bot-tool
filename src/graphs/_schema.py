from typing import TypedDict
from pydantic import BaseModel, Field

class QaBotState(TypedDict):
    """
    Represent state of the graph

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
        documents_relevant: relevance score of the documents to the question
        software_bug_or_user_feedback_relevant: relevance score of the question to software bugs or user feedback
    """

    question: str
    generation: str
    documents: list[str]
    documents_relevant: str
    software_bug_or_user_feedback_relevant: str

class IsItBugOrUserFeedbackRelevant(BaseModel):
    """Binary score for relevance check whether the question is about bug reports or user feedback"""

    binary_score: str = Field(
        description="Is the question related to software bugs or user feedback on the software? 'yes' or 'no'?"
    )

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieve documents"""

    binary_score: str = Field(
        description="Documents are relevant to the question. 'yes' or 'no'?"
    )

__all__ = ["QaBotState", "IsItBugOrUserFeedbackRelevant", "GradeDocuments"]