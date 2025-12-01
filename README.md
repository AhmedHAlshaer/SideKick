# SideKick

A personal AI sidekick that you can use to help you in everyday activities. Built with LangGraph, it uses AI agents with tool-calling capabilities to complete complex tasks.

## ✨ Features

- 🤖 **Intelligent AI Agent** - Powered by DeepSeek/OpenAI with tool-calling
- 🌐 **Web Browsing** - Can navigate and interact with websites
- 💻 **Code Execution** - Runs Python code to solve problems
- 🧠 **Long-term Memory** - Remembers facts and preferences across conversations
- 📊 **Google Sheets Logging** - Automatically logs all conversations to Google Sheets
- ⚡ **Streaming Responses** - Real-time updates as the agent works
- 🎯 **Success Criteria** - Define custom success criteria for tasks
- 🔄 **Self-Evaluation** - Agent evaluates its own work and iterates

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Create a `.env` file:

```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 3. Run the Server

```bash
python app/server.py
```

Visit `http://localhost:8000` in your browser.

## 📊 Google Sheets Integration (Optional)

Log all conversations to Google Sheets for analysis and monitoring!

**Quick Setup:**

1. Get Google Service Account credentials ([guide here](./QUICK_SHEETS_GUIDE.md))
2. Add to `.env`:
   ```bash
   GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
   ```
3. Test: `python test_sheets_connection.py`

See [GOOGLE_SHEETS_SETUP.md](./GOOGLE_SHEETS_SETUP.md) for detailed instructions.

## 📖 Documentation

- [Quick Start Guide](./QUICK_START.md) - Get started with SideKick
- [Code Explained](./CODE_EXPLAINED.md) - Understanding the codebase
- [Memory System](./MEMORY_SYSTEM.md) - How long-term memory works
- [Streaming Feature](./STREAMING_FEATURE.md) - Real-time streaming details
- [Google Sheets Setup](./GOOGLE_SHEETS_SETUP.md) - Conversation logging setup
- [Quick Sheets Guide](./QUICK_SHEETS_GUIDE.md) - 5-minute setup

## 🏗️ Architecture

```
SideKick
├── Worker Node - Main agent with tools
├── Tool Node - Executes tools (browser, code, etc.)
├── Evaluator Node - Checks success criteria
└── Memory Extractor - Stores long-term memories
```

## 🛠️ Built With

- **LangGraph** - Agent orchestration
- **LangChain** - LLM framework
- **FastAPI** - Web server
- **ChromaDB** - Vector database for memories
- **Playwright** - Browser automation
- **Google Sheets API** - Conversation logging

## 🔧 Development

### Run Tests
```bash
python test_sheets_connection.py
```

### View Memories
```bash
python view_memories.py
```

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Feel free to open issues or submit PRs.
