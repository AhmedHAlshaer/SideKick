# Quick Google Sheets Integration Guide

> **TL;DR:** Get conversation logging to Google Sheets in 5 minutes!

## 🚀 Quick Start (5 Steps)

### 1. Get Google Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable "Google Sheets API" and "Google Drive API"
3. Create Service Account → Download JSON key
4. Save as `google-sheets-credentials.json` in your project folder

### 2. Configure Environment

Create a `.env` file in your project root:

```bash
DEEPSEEK_API_KEY=your_key_here
GOOGLE_SHEETS_CREDENTIALS_PATH=/absolute/path/to/google-sheets-credentials.json
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Test Connection

```bash
python test_sheets_connection.py
```

### 5. Start Using!

```bash
python app/server.py
```

That's it! Your conversations will now be logged to Google Sheets automatically.

## 📊 What You Get

A spreadsheet with every conversation including:

- 📝 User messages and AI responses
- 🔧 Tools used
- ⏱️ Response times
- ✅ Success indicators
- 💾 Extracted memories
- 📅 Timestamps and metadata

## 🔍 View Your Data

After first run, check the console for:
```
✅ Connected to Google Sheets: Sidekick Conversations
   URL: https://docs.google.com/spreadsheets/d/...
```

Click that URL to see your conversation data!

## 📖 Need More Help?

See [GOOGLE_SHEETS_SETUP.md](./GOOGLE_SHEETS_SETUP.md) for:
- Detailed setup instructions
- Troubleshooting guide
- Security best practices
- Advanced usage examples

## 🔧 Troubleshooting Quick Fixes

**"Credentials file not found"**
→ Use absolute path in `.env` file

**"Permission denied"**  
→ Share your Google Sheet with the service account email (in JSON file)

**"API not enabled"**
→ Enable Google Sheets API and Google Drive API in Cloud Console

## 💡 Tips

- Leave `GOOGLE_SHEETS_URL` empty to auto-create a new sheet
- Check `test_sheets_connection.py` output for detailed diagnostics
- Data exports to CSV: File → Download → CSV in Google Sheets
- Summary worksheet created automatically with statistics

---

**Ready to go?** Run `python test_sheets_connection.py` to verify everything works! ✨

