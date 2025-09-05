#!/usr/bin/env python3
"""
API Key Setup Helper

This script helps you set up the required API keys for the advanced email orchestration system.
"""

import os
import sys
from pathlib import Path

def setup_anthropic_key():
    """Set up Anthropic API key."""
    print("🔑 Setting up Anthropic (Claude) API Key")
    print("=" * 40)
    
    current_key = os.getenv('ANTHROPIC_API_KEY')
    if current_key:
        print(f"✅ ANTHROPIC_API_KEY is already set: {current_key[:10]}...")
        return True
    
    print("To get your Anthropic API key:")
    print("1. Go to https://console.anthropic.com/")
    print("2. Sign up or log in")
    print("3. Go to 'API Keys' section")
    print("4. Create a new API key")
    print("")
    
    api_key = input("Enter your Anthropic API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️ Skipping Anthropic API key setup")
        print("💡 You can set it later with: export ANTHROPIC_API_KEY=your_key_here")
        return False
    
    # Validate key format
    if not api_key.startswith('sk-ant-'):
        print("⚠️ Warning: Anthropic API keys usually start with 'sk-ant-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Set for current session
    os.environ['ANTHROPIC_API_KEY'] = api_key
    
    # Suggest adding to shell profile
    print("\n✅ API key set for current session!")
    print("\n💡 To make this permanent, add this line to your shell profile:")
    print(f"export ANTHROPIC_API_KEY={api_key}")
    print("\nFor bash/zsh, add to ~/.bashrc or ~/.zshrc:")
    print(f"echo 'export ANTHROPIC_API_KEY={api_key}' >> ~/.bashrc")
    
    return True

def check_gmail_setup():
    """Check Gmail credentials setup."""
    print("\n📧 Checking Gmail Setup")
    print("=" * 40)
    
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_credentials.json')
    
    if os.path.exists(credentials_path):
        print(f"✅ Gmail credentials found: {credentials_path}")
        return True
    else:
        print(f"⚠️ Gmail credentials not found: {credentials_path}")
        print("💡 Run 'python setup_gmail.py' to set up Gmail integration")
        return False

def test_ai_connection():
    """Test AI connection."""
    print("\n🧪 Testing AI Connection")
    print("=" * 40)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return False
    
    try:
        # Import and test
        sys.path.append(str(Path(__file__).parent))
        from departments.communication.services.ai_classification_service import AIClassificationService
        
        ai_service = AIClassificationService(api_key)
        print("✅ AI service initialized successfully!")
        print("🤖 Claude AI is ready for advanced personalization")
        return True
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Advanced Email Orchestration - API Key Setup")
    print("=" * 50)
    
    # Setup Anthropic key
    anthropic_ok = setup_anthropic_key()
    
    # Check Gmail
    gmail_ok = check_gmail_setup()
    
    # Test AI if key is available
    if anthropic_ok:
        ai_ok = test_ai_connection()
    else:
        ai_ok = False
    
    # Summary
    print("\n📊 Setup Summary")
    print("=" * 20)
    print(f"Anthropic API: {'✅' if anthropic_ok else '❌'}")
    print(f"Gmail Setup: {'✅' if gmail_ok else '⚠️'}")
    print(f"AI Service: {'✅' if ai_ok else '❌'}")
    
    if anthropic_ok and ai_ok:
        print("\n🎉 All set! Your advanced email orchestration system is ready!")
        print("💡 Run: python advanced_communication_control.py")
    elif anthropic_ok:
        print("\n⚠️ AI key is set but service test failed")
        print("💡 Try running the advanced system anyway")
    else:
        print("\n⚠️ AI features will be limited without ANTHROPIC_API_KEY")
        print("💡 You can still use basic features")
    
    print("\n🎮 Next steps:")
    print("1. Run: python advanced_communication_control.py")
    print("2. Type 'help' for available commands")
    print("3. Type 'demo' for a full demonstration")

if __name__ == "__main__":
    main() 