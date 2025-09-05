#!/usr/bin/env python3
"""
Gmail Setup and Test Script

This script helps you:
1. Test Gmail API credentials
2. Authenticate with Gmail
3. Verify the connection works
4. Test basic email monitoring
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from departments.communication.services.gmail_service import GmailService


async def test_gmail_setup():
    """Test Gmail API setup and authentication."""
    print("🔧 Gmail API Setup and Test")
    print("=" * 50)
    
    # Check environment variable
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')
    print(f"Looking for credentials at: {credentials_path}")
    
    if not os.path.exists(credentials_path):
        print("❌ Gmail credentials file not found!")
        print("\nTo set up Gmail API credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the JSON file as 'gmail_credentials.json'")
        print(f"6. Place it at: {os.path.abspath(credentials_path)}")
        print("7. Set environment variable: export GMAIL_CREDENTIALS_PATH=gmail_credentials.json")
        return False
    
    print(f"✅ Found credentials file: {credentials_path}")
    
    # Test Gmail service initialization
    print("\n🔄 Testing Gmail service initialization...")
    gmail_service = GmailService(credentials_path=credentials_path)
    
    try:
        success = await gmail_service.initialize()
        
        if success:
            print("✅ Gmail service initialized successfully!")
            print(f"📧 Connected to: {gmail_service.email_address}")
            
            # Test basic email monitoring
            print("\n🔄 Testing email monitoring (checking last 5 emails)...")
            messages = await gmail_service.monitor_emails(query="", max_results=5)
            
            print(f"📬 Found {len(messages)} recent emails:")
            for i, msg in enumerate(messages[:3], 1):  # Show first 3
                print(f"  {i}. From: {msg.sender}")
                print(f"     Subject: {msg.subject}")
                print(f"     Snippet: {msg.snippet[:100]}...")
                print()
            
            if len(messages) > 3:
                print(f"  ... and {len(messages) - 3} more emails")
            
            print("✅ Gmail monitoring test successful!")
            return True
            
        else:
            print("❌ Failed to initialize Gmail service")
            print("This usually means:")
            print("- Credentials file is invalid")
            print("- Gmail API is not enabled")
            print("- OAuth consent screen not configured")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gmail service: {e}")
        print("\nCommon issues:")
        print("- First time setup requires browser authentication")
        print("- Gmail API not enabled in Google Cloud Console")
        print("- Invalid credentials file")
        print("- Network connectivity issues")
        return False


async def main():
    """Main setup function."""
    print("🚀 Gmail API Setup for Jarvis Communication System")
    print("=" * 60)
    
    success = await test_gmail_setup()
    
    if success:
        print("\n🎉 Gmail setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the communication system test: python test_communication_system.py")
        print("2. Set up Claude API key for AI classification")
        print("3. Configure WhatsApp/LinkedIn if needed")
        print("4. Start using the semantic chat interface")
    else:
        print("\n❌ Gmail setup failed. Please follow the instructions above.")
        print("\nFor help:")
        print("- Check the README.md in departments/communication/")
        print("- Verify your Google Cloud Console setup")
        print("- Make sure Gmail API is enabled")


if __name__ == "__main__":
    asyncio.run(main()) 