# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets logging for your Sidekick conversations. Once configured, all conversations will be automatically logged to a Google Sheet where you can analyze them like a Retool dataset.

## 📊 What Gets Logged

Every conversation turn is logged with the following information:

- **Timestamp** - When the conversation happened
- **Session ID** - Unique identifier for the conversation session
- **User Message** - What the user asked
- **Assistant Response** - What the AI responded
- **Success Criteria** - The success criteria for the task
- **Tools Used** - Which tools the agent used (e.g., browser, code execution)
- **Conversation Status** - completed, in_progress, error
- **Success Met** - Whether the success criteria was achieved
- **User Input Needed** - Whether the agent needs more input
- **Memories Extracted** - Facts extracted for long-term memory
- **Response Length** - Character count of the response
- **Turn Number** - Which turn in the conversation
- **Date & Time** - Parsed date and time for easy filtering
- **Duration** - How long the turn took in seconds

## 🚀 Setup Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Name it something like "Sidekick Logging"

### Step 2: Enable Google Sheets API

1. In your Google Cloud project, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click on it and click **Enable**
4. Also enable "Google Drive API" (needed for creating/accessing sheets)

### Step 3: Create a Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Name it "sidekick-sheets-logger"
4. Click **Create and Continue**
5. Skip the optional role selection (or add "Editor" role for broader access)
6. Click **Done**

### Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**
6. A JSON file will download - **save this file securely!**

### Step 5: Save the Credentials File

1. Move the downloaded JSON file to your Sidekick project directory
2. Rename it to something memorable like `google-sheets-credentials.json`
3. **Important:** Add this file to your `.gitignore` to avoid committing secrets!

```bash
# Add to .gitignore if not already there
echo "google-sheets-credentials.json" >> .gitignore
```

### Step 6: Create a Google Sheet (Optional)

You can either:

**Option A: Let Sidekick create a new sheet automatically**
- Skip this step, and Sidekick will create a new sheet on first run
- The sheet URL will be printed in the console

**Option B: Create your own sheet**
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "Sidekick Conversations"
4. Copy the URL from your browser
5. Share the sheet with your service account email (found in the JSON file as `client_email`)
   - Give it "Editor" permissions

### Step 7: Configure Environment Variables

1. Open your `.env` file in the `app` directory
2. Add these lines:

```bash
# Google Sheets Logging Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=/Users/mac/projects/SideKick/google-sheets-credentials.json
GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit

# Note: GOOGLE_SHEETS_URL is optional - if not provided, a new sheet will be created
```

**Important:** 
- Use the **absolute path** to your credentials file
- If you didn't create a sheet manually (Option A above), leave `GOOGLE_SHEETS_URL` empty or remove that line

### Step 8: Install Dependencies

```bash
cd /Users/mac/projects/SideKick
uv sync
```

This will install the new Google Sheets dependencies: `gspread`, `google-auth`, and `google-auth-oauthlib`.

### Step 9: Test the Setup

1. Start your Sidekick server:

```bash
python app/server.py
```

2. Look for these messages in the console:
   - ✅ `Connected to Google Sheets: Sidekick Conversations`
   - OR ✅ `Created new Google Sheet: Sidekick Conversations`

3. Have a conversation with Sidekick
4. Check your Google Sheet - you should see a new row with the conversation data!

## 📋 Understanding the Data

### Columns Explained

| Column | Description | Example |
|--------|-------------|---------|
| Timestamp | ISO format timestamp | 2024-11-27T14:30:45.123456 |
| Session ID | Unique conversation ID | 550e8400-e29b-41d4-a716-446655440000 |
| User Message | User's input | "What's the weather today?" |
| Assistant Response | AI's response | "I'll check the weather for you..." |
| Success Criteria | Task requirements | "Provide accurate weather info" |
| Tools Used | Tools invoked | "browser_navigate, execute_code" |
| Conversation Status | Status | completed, in_progress, error |
| Success Met | Yes/No | Yes |
| User Input Needed | Yes/No | No |
| Memories Extracted | JSON array | ["User likes weather updates"] |
| Response Length | Character count | 245 |
| Turn Number | Turn in conversation | 1, 2, 3... |
| Date | YYYY-MM-DD | 2024-11-27 |
| Time | HH:MM:SS | 14:30:45 |
| Duration | Seconds taken | 2.34 |

### Using the Data

**Filter by Date:**
- Use the Date column to filter conversations from specific days

**Analyze Success Rate:**
- Count "Yes" in the "Success Met" column
- The Summary worksheet has automatic calculations

**Find Long Responses:**
- Sort by "Response Length" to see detailed answers

**Track Tool Usage:**
- Filter by "Tools Used" to see which tools are most popular

**Identify Problem Areas:**
- Look for "Yes" in "User Input Needed" - these might indicate unclear tasks

## 🔧 Troubleshooting

### Error: "Google Sheets logging disabled: GOOGLE_SHEETS_CREDENTIALS_PATH not set"

**Solution:** Check that your `.env` file has the correct path to your credentials file.

### Error: "Google Sheets credentials file not found"

**Solution:** Verify the path in your `.env` file is correct and the file exists. Use absolute paths.

### Error: "Failed to initialize Google Sheets: Permission denied"

**Solution:** 
1. If using an existing sheet, make sure you've shared it with the service account email
2. The service account email is in your JSON file as `client_email`
3. Share the sheet with "Editor" permissions

### Error: "API has not been used in project"

**Solution:** Make sure you enabled both Google Sheets API and Google Drive API in your Google Cloud project.

### No data appearing in the sheet

**Solution:**
1. Check the console for error messages
2. Verify your internet connection
3. Check if the service account has edit access to the sheet

## 🎯 Advanced Usage

### Multiple Sheets

To log to different sheets for different purposes:

```python
# In your code
from sheets_logger import SheetsLogger

# Create a custom logger
custom_logger = SheetsLogger()
custom_logger.sheet_url = "https://docs.google.com/spreadsheets/d/ANOTHER_SHEET/edit"
custom_logger.initialize()
```

### Export to CSV

You can download the Google Sheet as CSV directly from Google Sheets:
- File → Download → Comma-separated values (.csv)

### Create Dashboards

Connect the Google Sheet to Google Data Studio or other BI tools for real-time dashboards.

### Automated Insights

The system creates a "Summary" worksheet with automatic calculations:
- Total conversations
- Success rate
- Average response length
- Average duration

## 🔐 Security Best Practices

1. **Never commit credentials:**
   ```bash
   # Always in .gitignore
   google-sheets-credentials.json
   *.json
   ```

2. **Rotate keys periodically:**
   - Delete old service account keys
   - Create new ones every few months

3. **Limit permissions:**
   - Only share sheets with the service account that needs access
   - Use "Editor" not "Owner" permissions

4. **Backup your data:**
   - Periodically export your sheet as CSV
   - Store backups securely

## 📞 Support

If you run into issues:
1. Check the console output for error messages
2. Verify all steps in this guide
3. Check that your credentials file is valid JSON
4. Ensure APIs are enabled in Google Cloud Console

Happy logging! 📊✨

