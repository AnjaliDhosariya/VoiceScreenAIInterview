from datetime import datetime
from typing import List, Dict, Any
from src.db.supabase_client import supabase

class SignalsService:
    """Handles real-time interview signals"""
    
    @staticmethod
    def calculate_signals(interview_id: str, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate interview signals from turns"""
        candidate_turns = [t for t in turns if t["speaker"] == "candidate"]
        agent_turns = [t for t in turns if t["speaker"] == "agent"]
        
        if not candidate_turns:
            return {
                "talk_ratio": 0.0,
                "avg_response_length": 0,
                "sentiment": "neutral",
                "speech_rate_wpm": 0,
                "call_quality_score": 85
            }
        
        # Calculate word counts
        candidate_words = sum(len(t["text"].split()) for t in candidate_turns)
        agent_words = sum(len(t["text"].split()) for t in agent_turns)
        total_words = candidate_words + agent_words
        
        talk_ratio = candidate_words / total_words if total_words > 0 else 0
        avg_response_length = candidate_words // len(candidate_turns) if candidate_turns else 0
        
        # Simple sentiment analysis (can be enhanced with LLM)
        sentiment = SignalsService._basic_sentiment(candidate_turns)
        
        # Simulated speech rate (assuming ~150 words per minute average)
        speech_rate_wpm = int(avg_response_length * 2.5)  # Mock calculation
        
        # Mock call quality
        call_quality_score = 85
        
        return {
            "talk_ratio": round(talk_ratio, 2),
            "avg_response_length": avg_response_length,
            "sentiment": sentiment,
            "speech_rate_wpm": speech_rate_wpm,
            "call_quality_score": call_quality_score
        }
    
    @staticmethod
    def _basic_sentiment(turns: List[Dict[str, Any]]) -> str:
        """LLM-based sentiment analysis for interview responses using Groq"""
        try:
            from groq import Groq
            from src.config import GROQ_API_KEY, GROQ_MODEL
            
            client = Groq(api_key=GROQ_API_KEY)
            
            # Combine all candidate responses
            text = " ".join([t["text"] for t in turns[:5]])  # First 5 responses
            
            if len(text) < 50:  # Too short to analyze
                return "neutral"
            
            prompt = f"""Analyze the overall sentiment/tone of these interview responses. 
            
Candidate responses:
"{text[:500]}"  

Consider:
- Professional tone and confidence level
- Enthusiasm and engagement
- Overall positivity vs negativity
- Note: Words like "challenge" or "difficult" are NEUTRAL in professional context

Return ONLY one word: positive, neutral, or negative

Sentiment:"""

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=GROQ_MODEL,
            )
            sentiment = chat_completion.choices[0].message.content.strip().lower()
            
            # Clean up response (sometimes LLM adds punctuation)
            sentiment = "".join(c for c in sentiment if c.isalpha())
            
            # Validate response
            if sentiment in ['positive', 'neutral', 'negative']:
                return sentiment
            else:
                return "neutral"
                
        except Exception as e:
            print(f"Sentiment analysis error: {e}, falling back to neutral")
            # Fallback: count clearly positive indicators
            text = " ".join([t["text"].lower() for t in turns])
            if any(word in text for word in ["excited", "passionate", "love", "excellent", "thrilled"]):
                return "positive"
            return "neutral"  # Default to neutral instead of trying keyword matching
    
    @staticmethod
    def save_signals(interview_id: str, signals: Dict[str, Any]):
        """Save calculated signals to database"""
        data = {
            "interview_id": interview_id,
            "talk_ratio": signals["talk_ratio"],
            "avg_response_length": signals["avg_response_length"],
            "sentiment": signals["sentiment"],
            "speech_rate_wpm": signals["speech_rate_wpm"],
            "call_quality_score": signals["call_quality_score"],
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("interview_signals").insert(data).execute()
    
    @staticmethod
    def get_signals(interview_id: str):
        """Get signals for an interview"""
        response = supabase.table("interview_signals").select("*").eq("interview_id", interview_id).execute()
        return response.data[0] if response.data else None
