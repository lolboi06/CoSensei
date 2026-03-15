"""
Example usage of DynamicClarificationGenerator.
Shows how to generate truly contextual clarification questions for ANY topic.
"""

from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR


def example_1_web_application():
    """Example: Building a web application - generates web-specific questions."""
    prompt = "Build a web app for tracking team tasks"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 1: Web Application")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_2_data_analysis():
    """Example: Data analysis task - generates data-specific questions."""
    prompt = "Analyze customer purchasing patterns from our sales data"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 2: Data Analysis")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_3_api_backend():
    """Example: API backend - generates API-specific questions."""
    prompt = "Create a REST API for managing inventory that integrates with our database"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 3: API Backend")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_4_bash_script():
    """Example: Bash script - generates system-specific questions."""
    prompt = "Write a script to automate backup of log files"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 4: Bash Script")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_5_mobile_app():
    """Example: Mobile app - generates mobile-specific questions."""
    prompt = "Build an iOS app that helps users track their fitness goals"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 5: Mobile App")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_6_vague_request():
    """Example: Vague request - generates fundamental questions."""
    prompt = "Help me with my project"
    
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(prompt, analysis)
    
    print("=" * 60)
    print("EXAMPLE 6: Vague Request (No specific keywords)")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Detected Categories: {analysis['relevant_categories']}\n")
    print(clarification_prompt)
    print()


def example_with_answer_extraction():
    """Example: Extract answers and build context."""
    prompt = "Build a scalable API that needs authentication"
    
    # Analyze and generate questions
    analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(prompt)
    print("=" * 60)
    print("EXAMPLE: Answer Extraction & Context Building")
    print("=" * 60)
    print(f"User Request: {prompt}\n")
    print(f"Questions Asked: {len(analysis['questions'])}\n")
    
    # Simulate user answers
    user_response = """
1. We need a REST API for a payment platform
2. Python with FastAPI
3. AWS
4. PostgreSQL database
5. High availability, <100ms latency
"""
    
    print("User Response:\n" + user_response)
    
    # Extract answers
    answers = DYNAMIC_CLARIFICATION_GENERATOR.extract_answers_from_response(user_response, analysis['num_questions'])
    print(f"\nExtracted Answers: {answers}\n")
    
    # Build context
    context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(prompt, analysis, answers)
    print(f"Generated Context:")
    for key, value in context.items():
        if not key.startswith('_'):
            print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    example_1_web_application()
    example_2_data_analysis()
    example_3_api_backend()
    example_4_bash_script()
    example_5_mobile_app()
    example_6_vague_request()
    example_with_answer_extraction()
