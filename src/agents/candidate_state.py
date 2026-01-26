from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Literal
from datetime import datetime

@dataclass
class Decision:
    """Represents an agent decision during the interview"""
    timestamp: str
    question_number: int
    decision_type: Literal["continue", "terminate", "add_followup", "difficulty", "skill_selection"]
    action: str  # The specific action taken
    reasoning: str  # Why the agent made this decision
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context

@dataclass
class CandidateState:
    """Tracks evolving candidate performance and interview context"""
    interview_id: str
    candidate_id: str
    job_id: str
    
    # Performance tracking
    overall_score: float = 0.0
    performance_trend: List[float] = field(default_factory=list)  # Score history
    question_count: int = 0
    
    # Signal tracking
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    struggle_count: int = 0  # Consecutive weak answers
    strong_answer_count: int = 0  # Consecutive strong answers
    
    # Adaptive context
    current_difficulty: Literal["easy", "medium", "hard"] = "medium"
    topics_covered: Set[str] = field(default_factory=set)
    skills_tested: Set[str] = field(default_factory=set)
    next_skill_to_test: str = ""  # Agent's decision for next technical question
    
    # Decision history
    decisions_made: List[Decision] = field(default_factory=list)
    
    # Question tracking
    last_question: str = ""
    last_question_type: str = ""
    last_answer: str = ""
    last_score: float = 0.0
    
    # State metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def avg_score(self) -> float:
        """Calculate average score from performance trend"""
        if not self.performance_trend:
            return 0.0
        return sum(self.performance_trend) / len(self.performance_trend)
    
    @property
    def recent_avg_score(self) -> float:
        """Calculate average of last 3 scores"""
        if not self.performance_trend:
            return 0.0
        recent = self.performance_trend[-3:]
        return sum(recent) / len(recent)
    
    def add_decision(self, decision: Decision):
        """Add a decision to history and update timestamp"""
        self.decisions_made.append(decision)
        self.last_updated = datetime.utcnow().isoformat()
    
    def update_performance(self, score: float):
        """Update performance metrics after evaluation"""
        self.performance_trend.append(score)
        self.last_score = score
        self.last_updated = datetime.utcnow().isoformat()
        
        # Update struggle/strong counters
        if score < 5.0:
            self.struggle_count += 1
            self.strong_answer_count = 0  # Reset
        elif score >= 8.0:
            self.strong_answer_count += 1
            self.struggle_count = 0  # Reset
        else:
            self.struggle_count = 0
            self.strong_answer_count = 0
        
        # Update overall score (weighted average, recent scores count more)
        self.overall_score = self.avg_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "interview_id": self.interview_id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "overall_score": self.overall_score,
            "performance_trend": self.performance_trend,
            "question_count": self.question_count,
            "red_flags": self.red_flags,
            "green_flags": self.green_flags,
            "struggle_count": self.struggle_count,
            "strong_answer_count": self.strong_answer_count,
            "current_difficulty": self.current_difficulty,
            "topics_covered": list(self.topics_covered),
            "skills_tested": list(self.skills_tested),
            "next_skill_to_test": self.next_skill_to_test,
            "decisions_made": [
                {
                    "timestamp": d.timestamp,
                    "question_number": d.question_number,
                    "decision_type": d.decision_type,
                    "action": d.action,
                    "reasoning": d.reasoning,
                    "context": d.context
                }
                for d in self.decisions_made
            ],
            "last_question": self.last_question,
            "last_question_type": self.last_question_type,
            "last_answer": self.last_answer,
            "last_score": self.last_score,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CandidateState':
        """Create CandidateState from dictionary"""
        decisions = [
            Decision(
                timestamp=d["timestamp"],
                question_number=d["question_number"],
                decision_type=d["decision_type"],
                action=d["action"],
                reasoning=d["reasoning"],
                context=d.get("context", {})
            )
            for d in data.get("decisions_made", [])
        ]
        
        return cls(
            interview_id=data["interview_id"],
            candidate_id=data["candidate_id"],
            job_id=data["job_id"],
            overall_score=data.get("overall_score", 0.0),
            performance_trend=data.get("performance_trend", []),
            question_count=data.get("question_count", 0),
            red_flags=data.get("red_flags", []),
            green_flags=data.get("green_flags", []),
            struggle_count=data.get("struggle_count", 0),
            strong_answer_count=data.get("strong_answer_count", 0),
            current_difficulty=data.get("current_difficulty", "medium"),
            topics_covered=set(data.get("topics_covered", [])),
            skills_tested=set(data.get("skills_tested", [])),
            next_skill_to_test=data.get("next_skill_to_test", ""),
            decisions_made=decisions,
            last_question=data.get("last_question", ""),
            last_question_type=data.get("last_question_type", ""),
            last_answer=data.get("last_answer", ""),
            last_score=data.get("last_score", 0.0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            last_updated=data.get("last_updated", datetime.utcnow().isoformat())
        )
