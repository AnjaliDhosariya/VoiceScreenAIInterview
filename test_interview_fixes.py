"""
Test script for interview logic fixes

Tests:
1. Recommendation logic with various question counts and scores
2. Verification that prompts contain anti-duplicate constraints
"""

import sys
sys.path.append('e:/VoiceScreenAI')

from src.services.summary_service import SummaryService

def test_recommendation_logic():
    """Test Suite 1: Recommendation threshold logic"""
    
    test_cases = [
        # (num_questions, overall_score, expected_result, description)
        (3, 76, "HOLD", "Early termination with high score"),
        (8, 76, "PROCEED", "Minimum questions with high score"),
        (5, 65, "HOLD", "Early termination with medium score"),
        (4, 45, "REJECT", "Early termination with low score"),
        (10, 65, "HOLD", "Full interview with medium score"),
        (8, 75, "PROCEED", "Edge case - exactly 8 questions, threshold score"),
        (7, 90, "HOLD", "Below minimum by 1, excellent score"),
        (2, 85, "HOLD", "Very early termination, high score"),
        (8, 60, "HOLD", "Minimum questions, borderline score"),
        (15, 80, "PROCEED", "Extended interview, strong score"),
    ]
    
    print("=" * 80)
    print("TEST SUITE 1: RECOMMENDATION LOGIC")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for num_q, score, expected, description in test_cases:
        result = SummaryService._determine_recommendation(score, num_q)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | Q={num_q:2d}, Score={score:2d} | Expected: {expected:7s} | Got: {result:7s}")
        print(f"       {description}")
        print()
    
    print("-" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    print()
    
    return passed, failed

def test_prompt_constraints():
    """Test Suite 2: Verify prompt constraints exist"""
    
    print("=" * 80)
    print("TEST SUITE 2: PROMPT CONSTRAINT VERIFICATION")
    print("=" * 80)
    print()
    
    from src.agents.question_generator_agent import QuestionGeneratorAgent
    
    # Read the source file to check prompts
    with open('e:/VoiceScreenAI/src/agents/question_generator_agent.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    checks = []
    
    # Check 1: Motivation prompt has background prohibition
    check1 = "DO NOT ask about their background/experience" in source
    checks.append(("Motivation prompt forbids background questions", check1))
    
    # Check 2: BAD examples in motivation
    check2 = "BAD EXAMPLES (AVOID):" in source and "Already covered in warmup" in source
    checks.append(("Motivation prompt has BAD examples", check2))
    
    # Check 3: General prompt has global constraint
    check3 = "CRITICAL: DO NOT ask about candidate's background, experience overview" in source
    checks.append(("General prompt has global background constraint", check3))
    
    # Check 4: Warmup still asks about background (should be true)
    check4 = "warmup" in source.lower() and "background" in source.lower()
    checks.append(("Warmup prompt mentions background (correct)", check4))
    
    passed = 0
    failed = 0
    
    for description, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        if result:
            passed += 1
        else:
            failed += 1
        print(f"{status} | {description}")
    
    print()
    print("-" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(checks)} checks")
    print("=" * 80)
    print()
    
    return passed, failed

if __name__ == "__main__":
    print()
    print("🧪 RUNNING INTERVIEW LOGIC FIX TESTS")
    print()
    
    # Run test suites
    rec_passed, rec_failed = test_recommendation_logic()
    prompt_passed, prompt_failed = test_prompt_constraints()
    
    # Summary
    total_passed = rec_passed + prompt_passed
    total_failed = rec_failed + prompt_failed
    total_tests = total_passed + total_failed
    
    print()
    print("=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%")
    print("=" * 80)
    
    if total_failed == 0:
        print()
        print("🎉 ALL TESTS PASSED! The fixes are working correctly.")
    else:
        print()
        print("⚠️  SOME TESTS FAILED. Please review the output above.")
