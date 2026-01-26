
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class CreateInterviewRequest(BaseModel):
    candidateId: str
    jobId: str
    channel: Literal["simulation", "voice"] = "simulation"
    consentRequired: bool = True

class CreateInterviewResponse(BaseModel):
    interviewId: str
    status: str
    nextStep: str

class DisclosureResponse(BaseModel):
    interviewId: str
    disclosureText: str
    statusAfter: str

class ConsentRequest(BaseModel):
    consent: Literal["yes", "no"]

class ConsentResponse(BaseModel):
    consentStatus: str
    status: str
    nextStep: Optional[str] = None

class NextQuestionResponse(BaseModel):
    turnNo: int
    questionType: str
    question: str
    expectedSignals: List[str]

class AnswerRequest(BaseModel):
    turnNo: int
    answer: str

class AnswerResponse(BaseModel):
    received: bool
    status: str
    nextStep: str

class InterviewScores(BaseModel):
    technical: int
    communication: int
    culture: int

class FinishInterviewResponse(BaseModel):
    interviewId: str
    recommendation: str
    overallScore: int
    scores: InterviewScores
    highlights: List[str]
    concerns: List[str]
    status: str

class QuestionGenerationInput(BaseModel):
    jobId: str
    history: List[Dict[str, Any]]
    difficulty: str
