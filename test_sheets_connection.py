"""
Quick test script to verify Google Sheets connection

Run this to verify your Google Sheets integration is working correctly.

Usage:
    python test_sheets_connection.py
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from dotenv import load_dotenv
from sheets_logger import SheetsLogger
from datetime import datetime

# Load environment variables
load_dotenv()

def test_connection():
    """Test the Google Sheets connection."""
    print("\n" + "="*60)
    print("🧪 Testing Google Sheets Connection")
    print("="*60 + "\n")
    
    # Check environment variables
    print("📋 Checking environment variables...")
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    sheet_url = os.getenv("GOOGLE_SHEETS_URL")
    
    if not creds_path:
        print("❌ GOOGLE_SHEETS_CREDENTIALS_PATH not set")
        print("   Add this to your .env file:")
        print("   GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json")
        return False
    
    print(f"✅ Credentials path: {creds_path}")
    
    if sheet_url:
        print(f"✅ Sheet URL: {sheet_url}")
    else:
        print("ℹ️  No sheet URL set - will create new sheet")
    
    # Check if credentials file exists
    print("\n📁 Checking credentials file...")
    if not Path(creds_path).exists():
        print(f"❌ Credentials file not found: {creds_path}")
        print("   Make sure the file exists and path is correct")
        return False
    
    print(f"✅ Credentials file found")
    
    # Try to initialize connection
    print("\n🔌 Initializing connection...")
    logger = SheetsLogger()
    
    if not logger.initialize():
        print("❌ Failed to initialize Google Sheets connection")
        print("   Check the error messages above for details")
        return False
    
    print("✅ Successfully connected to Google Sheets!")
    
    # Try to log a test entry
    print("\n📝 Logging test entry...")
    try:
        test_session_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        logger.log_conversation_turn(
            session_id=test_session_id,
            user_message="This is a test message",
            assistant_response="This is a test response",
            success_criteria="Testing Google Sheets integration",
            tools_used=["test_tool"],
            status="completed",
            success_met=True,
            user_input_needed=False,
            turn_number=1,
            duration=0.5
        )
        
        print("✅ Test entry logged successfully!")
        print(f"   Session ID: {test_session_id}")
        
        if logger.sheet:
            print(f"\n🔗 View your sheet at: {logger.sheet.url}")
        
    except Exception as e:
        print(f"❌ Failed to log test entry: {e}")
        return False
    
    # Try to read back data
    print("\n📖 Reading back recent entries...")
    try:
        recent = logger.get_recent_conversations(limit=5)
        print(f"✅ Retrieved {len(recent)} recent conversation(s)")
        
        if recent:
            print("\nMost recent entry:")
            print(f"  Timestamp: {recent[-1][0] if len(recent[-1]) > 0 else 'N/A'}")
            print(f"  Session ID: {recent[-1][1] if len(recent[-1]) > 1 else 'N/A'}")
            
    except Exception as e:
        print(f"⚠️  Could not read back data: {e}")
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)
    print("\n💡 Your Google Sheets integration is working correctly.")
    print("   Conversations will be automatically logged from now on.\n")
    
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

