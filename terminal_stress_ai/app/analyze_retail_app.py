"""
Analysis of retail offers mobile app using Dynamic Clarification System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR

# Your project request
user_request = 'Build a mobile app to get best offers around me from retail stores with Node.js backend and AWS Lambda'
user_answers = {
    'answer_1': 'Mobile App',
    'answer_2': 'Node JS with AWS Lambda backend',
    'answer_3': 'Location-based retail offers',
    'answer_4': 'Real-time offers from nearby stores'
}

# Analyze the request
analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_request)
print('=' * 70)
print('RETAIL OFFERS APP ANALYSIS')
print('=' * 70)
print('User Request: {}\n'.format(user_request))
print('Detected Categories: {}'.format(analysis['relevant_categories']))
print('Clarity Level: {} categories detected\n'.format(len(analysis['relevant_categories'])))

# Build context from answers
context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
    user_request, analysis, user_answers
)

print('Extracted Semantic Context:')
print('-' * 70)
for key, value in context.items():
    if not key.startswith('_'):
        print('  {:<35} {}'.format(key + ':', value))

print()
print('=' * 70)
print('PLATFORM RECOMMENDATION')
print('=' * 70)

categories = context.get('relevant_categories', [])
if 'interface' in categories and context.get('target_platform') == 'mobile':
    route = 'GeneratorAI_Mobile'
    print('Route: {}\n'.format(route))
    print('[BEST] - Mobile App is CORRECT choice because:')
    print('  ✓ Users want location-based offers (needs GPS)')
    print('  ✓ Real-time notifications ideal for mobile push')
    print('  ✓ Mobile users are target audience for shopping')
    print()
    print('Full Architecture Recommendations:')
    print('-' * 70)
    print('FRONTEND:')
    print('  > React Native or Flutter')
    print('    - iOS + Android from single codebase')
    print('    - Native GPS & location services')
    print('    - Push notification support')
    print()
    print('BACKEND:')
    print('  > Node.js + Express + AWS Lambda')
    print('    - Serverless = no server management')
    print('    - Auto-scales with demand')
    print('    - Great for high-latency operations')
    print()
    print('DATABASE:')
    print('  > DynamoDB + ElastiCache')
    print('    - DynamoDB: Serverless, auto-scales')
    print('    - Redis Cache: Fast offer lookups')
    print('    - TTL: Auto-expire old offers')
    print()
    print('LOCATION & MAPPING:')
    print('  > AWS Location Service + Google Maps')
    print('    - Geolocation: Find stores within radius')
    print('    - Geofencing: Notify users entering store zones')
    print('    - Route optimization: Best deals nearby')
    print()
    print('REAL-TIME:')
    print('  > AWS AppSync (GraphQL) or WebSocket')
    print('    - Push offers to users in real-time')
    print('    - Live offer updates as prices change')
    print()
    print('NOTIFICATIONS:')
    print('  > Firebase Cloud Messaging or AWS SNS')
    print('    - Push notifications for nearby deals')
    print('    - Geofence-triggered alerts')
    print()
    print('DEPLOYMENT:')
    print('  > AWS Architecture:')
    print('    - Lambda for API')
    print('    - API Gateway for routing')
    print('    - CloudFront for CDN')
    print('    - VPC for security')
    print()
    print('AUTHENTICATION:')
    print('  > AWS Cognito')
    print('    - User registration/login')
    print('    - OAuth integration (Google, Apple)')
    print()
    print('MONITORING:')
    print('  > CloudWatch + X-Ray')
    print('    - Performance monitoring')
    print('    - Error tracking')
    
    print()
    print('=' * 70)
    print('SCALABILITY CONSIDERATIONS')
    print('=' * 70)
    print('For location-based retail offers at scale:')
    print('  • Geospatial Queries: Use DynamoDB with geo-indexing')
    print('  • Caching Layer: Redis ElastiCache for hot offers')
    print('  • CDN: CloudFront for static content')
    print('  • Load Balancing: API Gateway auto-load balancing')
    print('  • Database Sharding: By geographic region')
    print('  • API Rate Limiting: Prevent abuse')
    
else:
    print('Route: GeneratorAI_General')
