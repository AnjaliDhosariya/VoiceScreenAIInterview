from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# Define the state schema
class InterviewState(TypedDict):
    interview_id: str
    candidate_id: str
    job_id: str
    status: Literal["CREATED", "DISCLOSURE_DONE", "CONSENT_GRANTED", "INTERVIEW_IN_PROGRESS", "COMPLETED", "SYNCED_TO_ATS", "ENDED"]
    consent_granted: bool
    current_turn: int
    max_turns: int
    questions_asked: Annotated[list, operator.add]
    answers_received: Annotated[list, operator.add]
    evaluation_scores: Annotated[list, operator.add]
    error: str | None

class InterviewFlowGraph:
    """LangGraph-based state machine for interview workflow"""
    
    def __init__(self):
        self.memory = MemorySaver()  # Initialize memory first
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the interview flow graph"""
        
        # Create the graph
        workflow = StateGraph(InterviewState)
        
        # Add nodes (states)
        workflow.add_node("created", self._handle_created)
        workflow.add_node("disclosure", self._handle_disclosure)
        workflow.add_node("consent", self._handle_consent)
        workflow.add_node("start_interview", self._handle_start_interview)
        workflow.add_node("ask_question", self._handle_ask_question)
        workflow.add_node("process_answer", self._handle_process_answer)
        workflow.add_node("evaluate", self._handle_evaluate)
        workflow.add_node("finish", self._handle_finish)
        workflow.add_node("sync_ats", self._handle_sync_ats)
        workflow.add_node("end", self._handle_end)
        
        # Set entry point
        workflow.set_entry_point("created")
        
        # Add edges (transitions)
        workflow.add_edge("created", "disclosure")
        workflow.add_edge("disclosure", "consent")
        
        # Conditional edge from consent
        workflow.add_conditional_edges(
            "consent",
            self._check_consent,
            {
                "granted": "start_interview",
                "denied": "end"
            }
        )
        
        workflow.add_edge("start_interview", "ask_question")
        workflow.add_edge("ask_question", "process_answer")
        workflow.add_edge("process_answer", "evaluate")
        
        # Conditional edge from evaluate
        workflow.add_conditional_edges(
            "evaluate",
            self._check_continue,
            {
                "continue": "ask_question",
                "finish": "finish"
            }
        )
        
        workflow.add_edge("finish", "sync_ats")
        workflow.add_edge("sync_ats", "end")
        workflow.add_edge("end", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    # Node handlers
    def _handle_created(self, state: InterviewState) -> InterviewState:
        """Handle CREATED state"""
        return {
            **state,
            "status": "CREATED",
            "current_turn": 0,
            "questions_asked": [],
            "answers_received": [],
            "evaluation_scores": []
        }
    
    def _handle_disclosure(self, state: InterviewState) -> InterviewState:
        """Handle DISCLOSURE state"""
        return {
            **state,
            "status": "DISCLOSURE_DONE"
        }
    
    def _handle_consent(self, state: InterviewState) -> InterviewState:
        """Handle CONSENT state"""
        # Consent is set externally
        if state.get("consent_granted"):
            return {**state, "status": "CONSENT_GRANTED"}
        else:
            return {**state, "status": "ENDED"}
    
    def _handle_start_interview(self, state: InterviewState) -> InterviewState:
        """Handle START_INTERVIEW state"""
        return {
            **state,
            "status": "INTERVIEW_IN_PROGRESS"
        }
    
    def _handle_ask_question(self, state: InterviewState) -> InterviewState:
        """Handle ASK_QUESTION state"""
        # Question generation happens externally
        return {
            **state,
            "current_turn": state["current_turn"] + 1
        }
    
    def _handle_process_answer(self, state: InterviewState) -> InterviewState:
        """Handle PROCESS_ANSWER state"""
        # Answer processing happens externally
        return state
    
    def _handle_evaluate(self, state: InterviewState) -> InterviewState:
        """Handle EVALUATE state"""
        # Evaluation happens externally
        return state
    
    def _handle_finish(self, state: InterviewState) -> InterviewState:
        """Handle FINISH state"""
        return {
            **state,
            "status": "COMPLETED"
        }
    
    def _handle_sync_ats(self, state: InterviewState) -> InterviewState:
        """Handle SYNC_ATS state"""
        return {
            **state,
            "status": "SYNCED_TO_ATS"
        }
    
    def _handle_end(self, state: InterviewState) -> InterviewState:
        """Handle END state"""
        return state
    
    # Conditional checkers
    def _check_consent(self, state: InterviewState) -> str:
        """Check if consent was granted"""
        return "granted" if state.get("consent_granted") else "denied"
    
    def _check_continue(self, state: InterviewState) -> str:
        """Check if interview should continue or finish"""
        max_turns = state.get("max_turns", 10)
        current_turn = state.get("current_turn", 0)
        
        if current_turn >= max_turns:
            return "finish"
        return "continue"
    
    def get_graph(self):
        """Get the compiled graph"""
        return self.graph
    
    def get_state(self, thread_id: str) -> InterviewState:
        """Get current state for a thread"""
        # This would retrieve from checkpointer
        pass
    
    def update_state(self, thread_id: str, updates: dict) -> InterviewState:
        """Update state for a thread"""
        # This would update in checkpointer
        pass


# Singleton instance
interview_graph = InterviewFlowGraph()
