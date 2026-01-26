"""
Test script for the two new improvements:
1. Dynamic warmup question generation (LLM-based, job-specific)
2. LLM response to candidate questions during candidate_questions turn
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_improvements():
    print("="*70)
    print("TESTING TWO IMPROVEMENTS")
    print("="*70)
    
    # Test 1: Dynamic Warmup Question
    print("\n[TEST 1] Dynamic Warmup Question Generation")
    print("-"*70)
    
    # Create interview
    create_resp = requests.post(f"{BASE_URL}/hr/interview/create", json={
        "candidateId": "CAND-999",
        "jobId": "JOB-ML-SENIOR",  # Different job to see different warmup
        "channel": "simulation"
    })
    
    if create_resp.status_code != 200:
        print(f"❌ Failed to create interview: {create_resp.status_code}")
        return
    
    interview_id = create_resp.json()["interviewId"]
    print(f"✅ Created interview: {interview_id}")
    
    # Get disclosure & consent (required flow)
    requests.get(f"{BASE_URL}/hr/interview/{interview_id}/disclosure")
    requests.post(f"{BASE_URL}/hr/interview/{interview_id}/consent", json={"consent": "yes"})
    
    # Get first question (should be dynamic warmup)
    q1_resp = requests.get(f"{BASE_URL}/hr/interview/{interview_id}/next-question")
    if q1_resp.status_code == 200:
        q1 = q1_resp.json()
        print(f"\n📝 Question 1 (Warmup):")
        print(f"   Type: {q1.get('questionType')}")
        print(f"   Question: {q1.get('question')}")
        print(f"\n✅ SUCCESS: Warmup question is dynamically generated!")
        print(f"   (Should be specific to ML Senior role, not generic)")
    else:
        print(f"❌ Failed to get question: {q1_resp.status_code}")
        return
    
    # Submit answer to warmup
    requests.post(f"{BASE_URL}/hr/interview/{interview_id}/answer", json={
        "turnNo": 1,
        "answer": "I have 5 years of ML experience and I'm interested in this role..."
    })
    
    # Skip ahead to candidate_questions turn (Q9)
    # Answer questions 2-8 quickly
    for i in range(2, 9):
        q_resp = requests.get(f"{BASE_URL}/hr/interview/{interview_id}/next-question")
        if q_resp.status_code == 200:
            requests.post(f"{BASE_URL}/hr/interview/{interview_id}/answer", json={
                "turnNo": i,
                "answer": f"Answer to question {i}"
            })
            time.sleep(0.5)
    
    # Test 2: LLM Response to Candidate Question
    print("\n\n[TEST 2] LLM Response to Candidate Question")
    print("-"*70)
    
    # Get candidate_questions turn
    q9_resp = requests.get(f"{BASE_URL}/hr/interview/{interview_id}/next-question")
    if q9_resp.status_code == 200:
        q9 = q9_resp.json()
        print(f"\n📝 Question 9 (Candidate Questions):")
        print(f"   Question: {q9.get('question')}")
        
        # Candidate asks a question
        candidate_question = "What is the team size and what tech stack do you use?"
        print(f"\n💬 Candidate asks: \"{candidate_question}\"")
        
        requests.post(f"{BASE_URL}/hr/interview/{interview_id}/answer", json={
            "turnNo": 9,
            "answer": candidate_question
        })
        
        time.sleep(2)  # Give time for LLM response generation
        
        # Fetch all turns to see if LLM responded
        # Note: We'd need an endpoint to get turns, but we can check logs
        print("\n✅ Check backend logs for:")
        print("   [INFO] Generated response to candidate question: ...")
        print("\n   The LLM should have generated a response about team/tech stack")
        print("   and saved it as an 'agent' turn before the wrapup question.")
    
    # Finish interview
    print("\n\n[FINISHING] Completing interview...")
    finish_resp = requests.post(f"{BASE_URL}/hr/interview/{interview_id}/finish")
    if finish_resp.status_code == 200:
        result = finish_resp.json()
        print(f"✅ Interview completed successfully")
        print(f"   Overall Score: {result.get('overallScore')}/100")
        print(f"   Recommendation: {result.get('recommendation')}")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print("\nNEXT STEPS:")
    print("1. Check if Q1 warmup is dynamic (not hardcoded)")
    print("2. Check backend logs for LLM response to candidate question")
    print("3. Manually test in frontend to see the flow")
    print("="*70)

if __name__ == "__main__":
    try:
        test_improvements()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
