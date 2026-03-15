"""
Interactive Chat Interface - Dynamic Clarification System
Real-time conversation with your projects using semantic analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR


class ContextFlowChat:
    """Interactive chat with Dynamic Clarification for project analysis"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_analysis = None
        self.current_context = None
    
    def print_welcome(self):
        print("\n" + "=" * 70)
        print("CONTEXTFLOW - Dynamic AI Project Analyzer")
        print("=" * 70)
        print("Chat with AI to analyze your project ideas")
        print()
        print("Commands:")
        print("  'exit' or 'quit'  - Leave chat")
        print("  'clear'           - Clear history")
        print("  'analysis'        - Show current analysis")
        print("  'context'         - Show extracted context")
        print("  'help'            - Show this help")
        print()
        print("-" * 70)
        print()
    
    def analyze_message(self, user_input):
        """Analyze user message and generate response"""
        
        # Store in history
        self.conversation_history.append(("user", user_input))
        
        # Analyze the input
        analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_input)
        self.current_analysis = analysis
        
        # Format response
        response = self.generate_response(user_input, analysis)
        self.conversation_history.append(("assistant", response))
        
        return response
    
    def generate_response(self, user_input, analysis):
        """Generate AI response based on analysis"""
        categories = analysis['relevant_categories']
        num_cats = len(categories)
        
        if num_cats == 0:
            # No clarity - ask fundamentals
            response = "I need more details about your project.\n\n"
            response += "Could you tell me:\n"
            response += "• What are you building?\n"
            response += "• What technology are you thinking about?\n"
            response += "• Where will it run? (web, mobile, backend, etc.)"
            
        else:
            # Build context even with partial info
            context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
                user_input, analysis, {"input": user_input}
            )
            self.current_context = context
            
            # Provide immediate recommendations
            response = "Understanding your project:\n"
            response += "• Categories detected: {}\n\n".format(", ".join(categories))
            response += self._generate_recommendations(context)
        
        return response
    
    def _generate_recommendations(self, context):
        """Generate tech recommendations based on context"""
        recs = "\n--- RECOMMENDATIONS ---\n"
        
        categories = context.get('relevant_categories', [])
        platform = context.get('target_platform', 'general')
        scale = context.get('project_scale', 'medium')
        user_input = context.get('original_request', '')
        
        recs += "Your Project Profile:\n"
        recs += "• Platform: {}\n".format(platform if platform else "web (default)")
        recs += "• Scale: {}\n".format(scale if scale else "medium")
        recs += "• Categories: {}\n".format(", ".join(categories) if categories else "general")
        
        # Domain-specific recommendations
        user_lower = user_input.lower()
        
        if 'ecommerce' in user_lower or 'e-commerce' in user_lower or 'shopping' in user_lower:
            recs += "\n[E-COMMERCE DETECTED]\n"
            recs += "• Frontend: React, Next.js, or Vue.js (for shopping cart UX)\n"
            recs += "• Backend: Node.js, Python Django, or .NET\n"
            recs += "• Database: PostgreSQL or MongoDB (for product catalog)\n"
            recs += "• Payment: Stripe, PayPal, or Square integration\n"
            recs += "• Hosting: AWS, Shopify, or self-hosted\n"
            recs += "• CDN: CloudFront for product images\n"
            recs += "• Search: Elasticsearch for product search\n"
            
        elif 'social' in user_lower or 'community' in user_lower:
            recs += "\n[SOCIAL/COMMUNITY DETECTED]\n"
            recs += "• Frontend: React or Vue for real-time updates\n"
            recs += "• Backend: Node.js or Python for social features\n"
            recs += "• Database: MongoDB for social graphs\n"
            recs += "• Real-time: WebSocket or Firebase\n"
            recs += "• Authentication: OAuth2 or JWT\n"
            
        elif 'api' in user_lower or 'backend' in user_lower:
            recs += "\n[BACKEND/API DETECTED]\n"
            recs += "• Framework: Express.js, FastAPI, or Django REST\n"
            recs += "• Database: PostgreSQL or DynamoDB\n"
            recs += "• Caching: Redis\n"
            recs += "• Documentation: Swagger/OpenAPI\n"
            recs += "• Deployment: Docker + Kubernetes or Lambda\n"
            
        else:
            # Generic recommendations
            recs += "\nSuggested Approach:\n"
            
            if 'interface' in categories:
                if platform == 'web':
                    recs += "• Frontend: React, Vue, or Next.js\n"
                    recs += "• Deployment: Vercel, Netlify, or AWS\n"
                elif platform == 'mobile':
                    recs += "• Frontend: React Native or Flutter\n"
                    recs += "• Deployment: App Store / Play Store\n"
            
            if 'integration' in categories:
                recs += "• Backend: REST API or GraphQL\n"
                recs += "• Integration: Webhooks, OAuth, or SDK\n"
            
            if 'data' in categories:
                if scale == 'enterprise':
                    recs += "• Database: PostgreSQL or DynamoDB\n"
                    recs += "• Cache: Redis or Memcached\n"
                else:
                    recs += "• Database: SQLite or MongoDB\n"
            
            if 'security' in categories:
                recs += "• Auth: OAuth2, JWT, or AWS Cognito\n"
                recs += "• Encryption: HTTPS, TLS, and data encryption\n"
        
        recs += "\nTell me more:\n"
        recs += "• How many users/products?\n"
        recs += "• Budget and timeline?\n"
        recs += "• Any specific tech preferences?"
        
        return recs
    
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
                    print("\nAssistant: Goodbye! Your project analysis is saved.")
                    break
                
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("\nAssistant: History cleared.\n")
                    continue
                
                elif user_input.lower() == 'analysis':
                    if self.current_analysis:
                        print("\nCurrent Analysis:")
                        print("Categories: {}".format(self.current_analysis['relevant_categories']))
                        print("Clarity: {} categories detected\n".format(len(self.current_analysis['relevant_categories'])))
                    else:
                        print("\nNo analysis yet. Describe your project first.\n")
                    continue
                
                elif user_input.lower() == 'context':
                    if self.current_context:
                        print("\nExtracted Context:")
                        for key, value in self.current_context.items():
                            if not key.startswith('_'):
                                print("  {}: {}".format(key, value))
                        print()
                    else:
                        print("\nNo context extracted yet.\n")
                    continue
                
                elif user_input.lower() == 'help':
                    self.print_welcome()
                    continue
                
                # Regular chat
                response = self.analyze_message(user_input)
                print(f"\nAssistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nAssistant: Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Try again.\n")


if __name__ == "__main__":
    chat = ContextFlowChat()
    chat.run()
