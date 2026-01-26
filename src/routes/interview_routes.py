from fastapi import APIRouter, HTTPException, status
from src.controllers.interview_controller import InterviewController
from src.schemas.interview_schema import (
    CreateInterviewRequest,
    CreateInterviewResponse,
    DisclosureResponse,
    ConsentRequest,
    ConsentResponse,
    NextQuestionResponse,
    AnswerRequest,
    AnswerResponse,
    FinishInterviewResponse
)

router = APIRouter(prefix="/hr/interview", tags=["Interview"])
controller = InterviewController()

@router.post("/create", response_model=CreateInterviewResponse)
async def create_interview(request: CreateInterviewRequest):
    """Create a new interview session"""
    try:
        result = controller.create_interview(
            request.candidateId,
            request.jobId,
            request.channel,
            request.consentRequired
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{interview_id}/disclosure", response_model=DisclosureResponse)
async def get_disclosure(interview_id: str):
    """Get disclosure script and request consent"""
    try:
        result = controller.get_disclosure(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{interview_id}/consent", response_model=ConsentResponse)
async def submit_consent(interview_id: str, request: ConsentRequest):
    """Submit consent response"""
    try:
        result = controller.submit_consent(interview_id, request.consent)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{interview_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(interview_id: str):
    """Get next interview question"""
    try:
        result = controller.get_next_question(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{interview_id}/answer", response_model=AnswerResponse)
async def submit_answer(interview_id: str, request: AnswerRequest):
    """Submit candidate answer"""
    try:
        result = controller.submit_answer(interview_id, request.turnNo, request.answer)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{interview_id}/finish", response_model=FinishInterviewResponse)
async def finish_interview(interview_id: str):
    """Finish interview and generate report"""
    try:
        result = controller.finish_interview(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{interview_id}/report")
async def get_report(interview_id: str):
    """Get full interview report"""
    try:
        result = controller.get_report(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{interview_id}/turns")
async def get_turns(interview_id: str):
    """Get full interview conversation history"""
    try:
        result = controller.get_turns(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Mock ATS Webhook
ats_router = APIRouter(prefix="/mock-ats", tags=["Mock ATS"])

@ats_router.post("/webhook")
async def ats_webhook(payload: dict):
    """Mock ATS webhook endpoint"""
    print(f"[MOCK ATS] Received interview data for candidate {payload.get('candidateId')}")
    print(f"[MOCK ATS] Recommendation: {payload.get('recommendation')}")
    print(f"[MOCK ATS] Overall Score: {payload.get('scores', {}).get('overall')}")
    return {"status": "success", "message": "Interview data received"}
