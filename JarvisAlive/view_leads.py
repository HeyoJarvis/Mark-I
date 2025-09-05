#!/usr/bin/env python3
"""
View stored leads from Redis and recent lead mining sessions.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

async def view_stored_leads():
    """View all stored leads from Redis."""
    
    print("🔍 Lead Viewer - Accessing Stored Leads")
    print("=" * 50)
    
    try:
        # Connect to Redis
        redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
        await redis_client.ping()
        print("✅ Connected to Redis")
        
        # Get all workflow result keys
        workflow_keys = await redis_client.keys("workflow_result:*")
        print(f"📊 Found {len(workflow_keys)} workflow results")
        
        lead_mining_results = []
        
        for key in workflow_keys:
            try:
                # Get workflow data
                workflow_data = await redis_client.hgetall(key)
                
                if workflow_data.get('agent_type') == 'lead_mining_agent':
                    print(f"\n🎯 Lead Mining Result: {workflow_data.get('workflow_id')}")
                    print(f"   Session: {workflow_data.get('session_id')}")
                    print(f"   Timestamp: {workflow_data.get('timestamp')}")
                    print(f"   Business Goal: {workflow_data.get('business_goal')}")
                    
                    # Parse results
                    try:
                        results = json.loads(workflow_data.get('results', '{}'))
                        qualified_leads = results.get('qualified_leads', [])
                        
                        print(f"   📈 Qualified Leads: {len(qualified_leads)}")
                        
                        if qualified_leads:
                            print(f"   📋 Lead Details:")
                            for i, lead in enumerate(qualified_leads[:3], 1):
                                if isinstance(lead, dict):
                                    name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                                    title = lead.get('job_title', 'Unknown Title')
                                    company = lead.get('company_name', 'Unknown Company')
                                    email = lead.get('email', 'No email')
                                    confidence = lead.get('confidence_score', 0)
                                    
                                    print(f"      {i}. {name} - {title}")
                                    print(f"         Company: {company}")
                                    print(f"         Email: {email}")
                                    print(f"         Confidence: {confidence:.2f}")
                                else:
                                    print(f"      {i}. {lead}")
                        
                        # Check for mining result details
                        mining_result = results.get('mining_result')
                        if mining_result:
                            if isinstance(mining_result, dict):
                                raw_leads = mining_result.get('leads_found', 0)
                                sources = mining_result.get('sources_used', [])
                                duration = mining_result.get('mining_duration_seconds', 0)
                                
                                print(f"   ⚡ Performance:")
                                print(f"      Raw leads found: {raw_leads}")
                                print(f"      Sources used: {sources}")
                                print(f"      Duration: {duration:.2f}s")
                        
                        lead_mining_results.append({
                            'workflow_id': workflow_data.get('workflow_id'),
                            'session_id': workflow_data.get('session_id'),
                            'timestamp': workflow_data.get('timestamp'),
                            'qualified_leads': qualified_leads,
                            'business_goal': workflow_data.get('business_goal')
                        })
                        
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Failed to parse results: {e}")
                        
            except Exception as e:
                print(f"❌ Error processing {key}: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   Total lead mining sessions: {len(lead_mining_results)}")
        total_qualified_leads = sum(len(result['qualified_leads']) for result in lead_mining_results)
        print(f"   Total qualified leads across all sessions: {total_qualified_leads}")
        
        # Show recent sessions
        if lead_mining_results:
            print(f"\n📅 Recent Sessions:")
            sorted_results = sorted(lead_mining_results, key=lambda x: x['timestamp'], reverse=True)
            for result in sorted_results[:3]:
                print(f"   • {result['workflow_id']}: {len(result['qualified_leads'])} leads ({result['business_goal']})")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ Error accessing Redis: {e}")

if __name__ == "__main__":
    asyncio.run(view_stored_leads())
