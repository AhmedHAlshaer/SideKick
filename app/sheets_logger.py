"""
Google Sheets Logger for Sidekick Conversations

Logs all conversations between users and the AI agent to Google Sheets
for analysis and monitoring. Creates a Retool-style dataset.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import os
from pathlib import Path


class SheetsLogger:
    """
    Logs conversations to Google Sheets for easy viewing and analysis.
    
    Setup:
    1. Create a Google Cloud Project
    2. Enable Google Sheets API
    3. Create a Service Account and download JSON key
    4. Share your Google Sheet with the service account email
    5. Set GOOGLE_SHEETS_CREDENTIALS_PATH in .env
    6. Set GOOGLE_SHEETS_URL in .env (optional, will create new sheet if not provided)
    """
    
    def __init__(self):
        self.client = None
        self.sheet = None
        self.worksheet = None
        self.enabled = False
        self.credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
        self.sheet_url = os.getenv("GOOGLE_SHEETS_URL")
        
    def initialize(self) -> bool:
        """
        Initialize connection to Google Sheets.
        Returns True if successful, False otherwise.
        """
        try:
            if not self.credentials_path:
                print("⚠️  Google Sheets logging disabled: GOOGLE_SHEETS_CREDENTIALS_PATH not set")
                return False
            
            # Check if credentials file exists
            if not Path(self.credentials_path).exists():
                print(f"⚠️  Google Sheets credentials file not found: {self.credentials_path}")
                return False
            
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Authenticate
            creds = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scope
            )
            self.client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            if self.sheet_url:
                # Open existing sheet
                self.sheet = self.client.open_by_url(self.sheet_url)
                print(f"✅ Connected to Google Sheets: {self.sheet.title}")
            else:
                # Create new sheet
                self.sheet = self.client.create("Sidekick Conversations")
                print(f"✅ Created new Google Sheet: {self.sheet.title}")
                print(f"   URL: {self.sheet.url}")
                print(f"   Add this to your .env: GOOGLE_SHEETS_URL={self.sheet.url}")
            
            # Get or create the main worksheet
            try:
                self.worksheet = self.sheet.worksheet("Conversations")
            except gspread.exceptions.WorksheetNotFound:
                self.worksheet = self.sheet.add_worksheet(
                    title="Conversations",
                    rows=1000,
                    cols=15
                )
                # Add headers
                self._initialize_headers()
            
            self.enabled = True
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to initialize Google Sheets: {e}")
            self.enabled = False
            return False
    
    def _initialize_headers(self):
        """Set up column headers for the conversation log."""
        headers = [
            "Timestamp",
            "Session ID",
            "User Message",
            "Assistant Response",
            "Success Criteria",
            "Tools Used",
            "Conversation Status",
            "Success Met",
            "User Input Needed",
            "Memories Extracted",
            "Response Length",
            "Turn Number",
            "Date",
            "Time",
            "Duration (seconds)"
        ]
        self.worksheet.update('A1:O1', [headers])
        
        # Format header row
        self.worksheet.format('A1:O1', {
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
            "textFormat": {
                "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "fontSize": 11,
                "bold": True
            },
            "horizontalAlignment": "CENTER"
        })
    
    def log_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        success_criteria: str = "",
        tools_used: List[str] = None,
        status: str = "completed",
        success_met: bool = False,
        user_input_needed: bool = False,
        memories_extracted: List[str] = None,
        turn_number: int = 1,
        duration: float = 0.0,
        metadata: Dict[str, Any] = None
    ):
        """
        Log a single conversation turn to Google Sheets.
        
        Args:
            session_id: Unique identifier for this conversation session
            user_message: What the user said
            assistant_response: What the assistant responded
            success_criteria: The success criteria for this task
            tools_used: List of tool names that were used
            status: Status of the conversation (completed, in_progress, error)
            success_met: Whether success criteria was met
            user_input_needed: Whether user input is needed to continue
            memories_extracted: Facts extracted for long-term memory
            turn_number: Which turn in the conversation this is
            duration: How long this turn took (in seconds)
            metadata: Additional metadata to store as JSON
        """
        if not self.enabled:
            return
        
        try:
            now = datetime.now()
            timestamp = now.isoformat()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            # Format tools and memories as readable strings
            tools_str = ", ".join(tools_used) if tools_used else "None"
            memories_str = json.dumps(memories_extracted) if memories_extracted else "None"
            
            # Calculate response length
            response_length = len(assistant_response)
            
            row = [
                timestamp,
                session_id,
                user_message,
                assistant_response,
                success_criteria,
                tools_str,
                status,
                "Yes" if success_met else "No",
                "Yes" if user_input_needed else "No",
                memories_str,
                response_length,
                turn_number,
                date_str,
                time_str,
                round(duration, 2)
            ]
            
            # Append row to sheet
            self.worksheet.append_row(row, value_input_option='RAW')
            print(f"📊 Logged conversation turn to Google Sheets (Session: {session_id[:8]}...)")
            
        except Exception as e:
            print(f"⚠️  Failed to log to Google Sheets: {e}")
    
    def log_conversation_batch(
        self,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ):
        """
        Log an entire conversation history at once.
        
        Args:
            session_id: Unique identifier for this conversation session
            conversation_history: List of message dictionaries with 'role' and 'content'
            metadata: Additional metadata about the conversation
        """
        if not self.enabled:
            return
        
        try:
            turn_number = 0
            user_msg = ""
            
            for message in conversation_history:
                if message.get("role") == "user":
                    user_msg = message.get("content", "")
                    turn_number += 1
                    
                elif message.get("role") == "assistant":
                    assistant_msg = message.get("content", "")
                    
                    self.log_conversation_turn(
                        session_id=session_id,
                        user_message=user_msg,
                        assistant_response=assistant_msg,
                        success_criteria=metadata.get("success_criteria", "") if metadata else "",
                        turn_number=turn_number,
                        status="completed"
                    )
                    
                    user_msg = ""  # Reset for next turn
                    
        except Exception as e:
            print(f"⚠️  Failed to batch log to Google Sheets: {e}")
    
    def get_recent_conversations(self, limit: int = 10) -> List[List[Any]]:
        """
        Retrieve recent conversations from the sheet.
        
        Args:
            limit: Number of recent conversations to retrieve
            
        Returns:
            List of rows (each row is a list of cell values)
        """
        if not self.enabled:
            return []
        
        try:
            # Get all values
            all_values = self.worksheet.get_all_values()
            
            # Return last N rows (excluding header)
            return all_values[-limit:] if len(all_values) > limit else all_values[1:]
            
        except Exception as e:
            print(f"⚠️  Failed to retrieve conversations: {e}")
            return []
    
    def create_summary_worksheet(self):
        """
        Create a summary worksheet with statistics and insights.
        """
        if not self.enabled:
            return
        
        try:
            # Check if summary sheet exists
            try:
                summary_ws = self.sheet.worksheet("Summary")
            except gspread.exceptions.WorksheetNotFound:
                summary_ws = self.sheet.add_worksheet(
                    title="Summary",
                    rows=100,
                    cols=10
                )
            
            # Add summary formulas
            summary_ws.update('A1', 'Sidekick Conversation Summary')
            summary_ws.update('A3', 'Total Conversations')
            summary_ws.update('B3', f'=COUNTA(Conversations!A:A)-1')  # Count rows minus header
            
            summary_ws.update('A4', 'Success Rate')
            summary_ws.update('B4', f'=COUNTIF(Conversations!H:H,"Yes")/COUNTA(Conversations!H:H)')
            
            summary_ws.update('A5', 'Average Response Length')
            summary_ws.update('B5', f'=AVERAGE(Conversations!K:K)')
            
            summary_ws.update('A6', 'Average Duration (seconds)')
            summary_ws.update('B6', f'=AVERAGE(Conversations!O:O)')
            
            print("✅ Created summary worksheet")
            
        except Exception as e:
            print(f"⚠️  Failed to create summary: {e}")


# Global instance
_sheets_logger = None


def get_sheets_logger() -> SheetsLogger:
    """
    Get or create the global SheetsLogger instance.
    """
    global _sheets_logger
    if _sheets_logger is None:
        _sheets_logger = SheetsLogger()
        _sheets_logger.initialize()
    return _sheets_logger


def log_conversation(
    session_id: str,
    user_message: str,
    assistant_response: str,
    **kwargs
):
    """
    Convenience function to log a conversation turn.
    """
    logger = get_sheets_logger()
    logger.log_conversation_turn(
        session_id=session_id,
        user_message=user_message,
        assistant_response=assistant_response,
        **kwargs
    )

