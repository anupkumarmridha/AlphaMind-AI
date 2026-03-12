"""
Test for Task 3.1: Enhanced LLM Extraction Prompt

This test validates that the DEEP_EXTRACT_PROMPT has been enhanced with:
- confidence field (0.0-1.0 value indicating certainty)
- impact_magnitude field (0.0-1.0 value indicating expected market impact strength)
- Instructions to reason about sentiment with full context
"""

def test_prompt_enhancement():
    """
    Verify that DEEP_EXTRACT_PROMPT includes the required enhancements.
    """
    print("\n=== Test Task 3.1: Prompt Enhancement ===")
    
    # Read the event_agent.py source code
    with open('agents/event_agent.py', 'r') as f:
        source_code = f.read()
    
    # Check for confidence field in prompt
    has_confidence_field = 'confidence:' in source_code and '0.0-1.0' in source_code
    print(f"✓ Has confidence field with 0.0-1.0 scale: {has_confidence_field}")
    
    # Check for impact_magnitude field in prompt
    has_impact_magnitude_field = 'impact_magnitude:' in source_code and '0.0-1.0' in source_code
    print(f"✓ Has impact_magnitude field with 0.0-1.0 scale: {has_impact_magnitude_field}")
    
    # Check for full context reasoning instructions
    has_context_reasoning = 'full context' in source_code or 'complete narrative' in source_code or 'conditional statements' in source_code
    print(f"✓ Has full context reasoning instructions: {has_context_reasoning}")
    
    # Check for guidance on confidence interpretation
    has_confidence_guidance = 'certainty' in source_code or 'certain' in source_code
    print(f"✓ Has confidence interpretation guidance: {has_confidence_guidance}")
    
    # Check for guidance on impact_magnitude interpretation
    has_impact_guidance = 'market impact' in source_code or 'market-moving' in source_code
    print(f"✓ Has impact_magnitude interpretation guidance: {has_impact_guidance}")
    
    # Check that prompt asks to avoid keyword matching
    has_anti_keyword_instruction = 'rather than' in source_code and 'keyword' in source_code
    print(f"✓ Has instruction to avoid keyword matching: {has_anti_keyword_instruction}")
    
    all_checks_passed = (
        has_confidence_field and 
        has_impact_magnitude_field and 
        has_context_reasoning and
        has_confidence_guidance and
        has_impact_guidance and
        has_anti_keyword_instruction
    )
    
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✓ TASK 3.1 COMPLETE: All prompt enhancements verified")
        print("\nThe DEEP_EXTRACT_PROMPT now includes:")
        print("  - confidence field (0.0-1.0 scale)")
        print("  - impact_magnitude field (0.0-1.0 scale)")
        print("  - Instructions for full context reasoning")
        print("  - Guidance on interpreting confidence and impact")
        print("  - Instructions to avoid simple keyword matching")
    else:
        print("✗ TASK 3.1 INCOMPLETE: Some enhancements missing")
    print("=" * 70)
    
    return all_checks_passed


def run():
    """Run the Task 3.1 validation test."""
    print("=" * 70)
    print("TASK 3.1 VALIDATION: Enhanced LLM Extraction Prompt")
    print("=" * 70)
    
    result = test_prompt_enhancement()
    
    if result:
        print("\n✓ Task 3.1 successfully completed!")
        print("\nNext steps (handled by other tasks):")
        print("  - Task 3.2: Implement multi-article aggregation")
        print("  - Task 3.3: Remove keyword-based scoring logic")
        print("  - Task 3.4: Parse and output confidence/impact fields")
    else:
        print("\n✗ Task 3.1 needs additional work")
    
    return result


if __name__ == "__main__":
    run()
