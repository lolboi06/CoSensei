"""
ContextFlow Chat - Dual Grok AI Integration
Generator AI (grok-3-mini) + Second AI (grok-3) for project analysis
"""

import sys
import os
import json
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR


# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '.terminal_stress_ai_config.json')
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)


class GrokAIClient:
    """Client for Grok API"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.x.ai/v1/chat/completions"
    
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Grok API"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant for project analysis."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(self.endpoint, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return f"Error: {response.status_code} - {response.text}"
        
        except ImportError:
            return "[Requests library not installed - using mock response]"
        except Exception as e:
            return f"API Error: {str(e)}"


class ContextFlowDualAI:
    """Dual Grok AI Chat - Generator AI + Second AI"""
    
    def __init__(self):
        self.generator_ai = GrokAIClient(
            CONFIG['generator_ai']['api_key'],
            CONFIG['generator_ai']['model']
        )
        self.second_ai = GrokAIClient(
            CONFIG['second_ai']['api_key'],
            CONFIG['second_ai']['model']
        )
        self.conversation_history = []
        self.current_analysis = None
    
    def print_welcome(self):
        print("\n" + "=" * 70)
        print("CONTEXTFLOW - Dual Grok AI Project Analyzer")
        print("=" * 70)
        print(f"Generator AI: {CONFIG['generator_ai']['model']}")
        print(f"Second AI: {CONFIG['second_ai']['model']}")
        print()
        print("Commands:")
        print("  'exit' or 'quit'  - Leave chat")
        print("  'analyze'         - Show semantic analysis")
        print("  'grok1'           - Ask Generator AI (grok-3-mini)")
        print("  'grok2'           - Ask Second AI (grok-3)")
        print("  'help'            - Show this help")
        print()
        print("-" * 70)
        print()
    
    def analyze_project(self, user_input: str) -> Dict[str, Any]:
        """Analyze project using Dynamic Clarification"""
        analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_input)
        context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
            user_input, analysis, {"input": user_input}
        )
        self.current_analysis = analysis
        return context
    
    def get_generator_ai_recommendation(self, context: Dict[str, Any], user_request: str) -> str:
        """Get recommendation from Generator AI (grok-3-mini)"""
        prompt = f"""Based on this project request, provide tech stack recommendations:

Project: {user_request}
Detected Categories: {context.get('relevant_categories', [])}
Platform: {context.get('target_platform', 'general')}
Scale: {context.get('project_scale', 'medium')}

Provide:
1. Frontend recommendation
2. Backend recommendation
3. Database recommendation
4. Deployment strategy

Be concise and specific."""
        
        print("\n[Generator AI (grok-3-mini) thinking...]")
        response = self.generator_ai.generate(prompt, max_tokens=600)
        return response
    
    def get_second_ai_review(self, context: Dict[str, Any], user_request: str, generator_recommendation: str) -> str:
        """Get review/alternative from Second AI (grok-3)"""
        prompt = f"""Review this tech recommendation and provide insights:

Project: {user_request}
Scale: {context.get('project_scale', 'medium')}

Generator AI Recommended:
{generator_recommendation}

Please provide:
1. Validation of the recommendation
2. Alternative approaches
3. Potential challenges
4. Cost/performance considerations

Be concise and practical."""
        
        print("[Second AI (grok-3) reviewing...]")
        response = self.second_ai.generate(prompt, max_tokens=600)
        return response
    
    def run_dual_analysis(self, user_input: str) -> None:
        """Run full dual AI analysis"""
        print("\n" + "=" * 70)
        print("DUAL AI ANALYSIS")
        print("=" * 70)
        
        # Step 1: Analyze with Dynamic Clarification
        print("\n[Step 1: Semantic Analysis]")
        context = self.analyze_project(user_input)
        print(f"Categories Detected: {context.get('relevant_categories', [])}")
        print(f"Platform: {context.get('target_platform', 'general')}")
        print(f"Scale: {context.get('project_scale', 'medium')}")
        
        # Step 2: Get Generator AI recommendation
        print("\n[Step 2: Generator AI Tech Stack]")
        gen_rec = self.get_generator_ai_recommendation(context, user_input)
        print("\nGenerator AI Recommendation:")
        print(gen_rec)
        
        # Step 3: Get Second AI review
        print("\n[Step 3: Second AI Review & Insights]")
        sec_rec = self.get_second_ai_review(context, user_input, gen_rec)
        print("\nSecond AI Review:")
        print(sec_rec)
        
        print("\n" + "=" * 70)
    
    def run(self):
        """Main chat loop"""
        self.print_welcome()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    print("\nAssistant: Analysis saved. Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self.print_welcome()
                    continue
                
                elif user_input.lower() == 'analyze':
                    if self.current_analysis:
                        print(f"\nCategories: {self.current_analysis['relevant_categories']}")
                        print(f"Clarity: {len(self.current_analysis['relevant_categories'])} categories\n")
                    else:
                        print("\nNo analysis yet. Describe your project first.\n")
                    continue
                
                elif user_input.lower() == 'grok1':
                    prompt = input("Ask Generator AI (grok-3-mini): ").strip()
                    if prompt:
                        response = self.generator_ai.generate(prompt)
                        print(f"\nGenerator AI:\n{response}\n")
                    continue
                
                elif user_input.lower() == 'grok2':
                    prompt = input("Ask Second AI (grok-3): ").strip()
                    if prompt:
                        response = self.second_ai.generate(prompt)
                        print(f"\nSecond AI:\n{response}\n")
                    continue
                
                # Regular project analysis with dual AI
                self.run_dual_analysis(user_input)
                
            except KeyboardInterrupt:
                print("\n\nAssistant: Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Try again.\n")


if __name__ == "__main__":
    chat = ContextFlowDualAI()
    chat.run()
