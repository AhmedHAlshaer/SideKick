# 🚀 Quick Start Guide

Everything you need to know to use and understand your Sidekick!

---

## 📋 What You Have

Your Sidekick is now a **production-ready AI personal assistant** with:

✅ **Web browsing** - Can navigate websites and extract information  
✅ **Email sending** - SendGrid integration (alshaerahmed8003@gmail.com → ahmealsh@iu.edu)  
✅ **Push notifications** - Pushover alerts  
✅ **Web search** - Google Serper API  
✅ **Wikipedia** - Knowledge lookup  
✅ **File management** - Read/write files in sandbox  
✅ **Python execution** - Run code on the fly  
✅ **Long-term memory** - Remembers across sessions (ChromaDB + local embeddings)  

---

## 🎮 How to Use

### **1. Start Your Sidekick**

```bash
cd /Users/mac/projects/SideKick/app
uv run app.py
```

Opens in browser at `http://127.0.0.1:7860`

### **2. View Your Memories**

```bash
cd /Users/mac/projects/SideKick
uv run view_memories.py
```

**Options:**
1. View all memories
2. Search for specific memories  
3. Add a manual memory
4. Clear all memories (dangerous!)
5. Get memory statistics
6. Exit

### **3. Example Interactions**

**Test Memory System:**
```
You: "I'm a student at Indiana University studying AI. I love Python!"
Sidekick: [Completes task and stores these facts]

[Later, in a new session...]
You: "Help me with a coding project"
Sidekick: [Recalls IU, AI, Python preference and gives tailored help!]
```

**Test Email:**
```
You: "Send me an email with subject 'Test' and say hello"
Success Criteria: "Email should be sent successfully"
Sidekick: [Uses send_email tool and sends it!]
```

**Test Web Browsing:**
```
You: "Go to python.org and tell me the latest Python version"
Success Criteria: "Get the current Python version number"
Sidekick: [Opens browser, navigates, extracts info]
```

**Test Research:**
```
You: "Research the latest AI news and email me a summary"
Success Criteria: "Summary should include at least 3 recent developments"
Sidekick: [Searches web, compiles summary, sends email]
```

---

## 📁 Project Structure

```
SideKick/
├── app/
│   ├── app.py              # 🖥️  Gradio UI (30 lines)
│   ├── sidekick.py         # 🧠 Agent logic (360 lines) - THE BRAIN
│   ├── sidekick_tools.py   # 🛠️  Tool definitions (90 lines)
│   └── memory_manager.py   # 💾 Memory system (210 lines)
│
├── chroma_db/              # 📚 Vector database (auto-created)
│   └── [ChromaDB files]
│
├── view_memories.py        # 🔍 Memory viewer tool
├── pyproject.toml          # 📦 Dependencies
│
├── MEMORY_SYSTEM.md        # 📖 Memory documentation
├── CODE_EXPLAINED.md       # 🎓 Complete code tutorial
├── QUICK_START.md          # 🚀 This file!
└── README.md               # 📄 Project overview
```

---

## 🧠 Understanding Your Code

### **Quick Mental Model**

```
┌─────────────────────────────────────────────────┐
│  USER INTERFACE (app.py)                        │
│  - Gradio web UI                                │
│  - Handles user input/output                    │
└──────────────┬──────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│  AGENT BRAIN (sidekick.py)                      │
│  ┌─────────────────────────────────────────┐   │
│  │ START → Worker → Router → ...          │   │
│  │          ↓         ↓                     │   │
│  │        Tools    Evaluator               │   │
│  │                    ↓                     │   │
│  │            Memory Extractor → END       │   │
│  └─────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│  CAPABILITIES                                    │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ TOOLS        │  │ MEMORY       │            │
│  │ - Browser    │  │ - ChromaDB   │            │
│  │ - Email      │  │ - Embeddings │            │
│  │ - Search     │  │ - Recall     │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
```

### **The Agent Loop**

```
1. USER: "Research AI and email me"
2. WORKER: "I need to search and send email"
3. ROUTER: "Worker wants tools"
4. TOOLS: [Executes search tool]
5. WORKER: "Got results, need email tool"  
6. ROUTER: "Worker wants tools again"
7. TOOLS: [Executes send_email tool]
8. WORKER: "Done! Email sent with research"
9. ROUTER: "No more tools, go to evaluator"
10. EVALUATOR: "Success criteria met ✅"
11. MEMORY_EXTRACTOR: "Store: User interested in AI"
12. END: Return to user
```

---

## 🎓 Learning Resources

### **Read These in Order:**

1. **QUICK_START.md** (this file) - Overview and usage
2. **CODE_EXPLAINED.md** - Deep dive into every concept
3. **MEMORY_SYSTEM.md** - How memory works

### **Key Concepts to Master:**

**Beginner Level:**
- ✅ What is an AI agent?
- ✅ How do tools work?
- ✅ What is async/await?

**Intermediate Level:**
- ✅ LangGraph state machines
- ✅ Node and routing patterns
- ✅ Tool integration

**Advanced Level:**
- ✅ Vector embeddings
- ✅ Semantic search
- ✅ Memory extraction & retrieval

**Read CODE_EXPLAINED.md for detailed explanations of each!**

---

## 🔧 Configuration

### **Environment Variables**

Create/edit `.env` file:
```bash
# Required
DEEPSEEK_API_KEY=your_key_here

# Optional tools
SENDGRID_API_KEY=your_key_here
PUSHOVER_TOKEN=your_token_here
PUSHOVER_USER=your_user_here
SERPER_API_KEY=your_key_here
```

### **Customize Memory**

Edit `sidekick.py`:
```python
# Change memory retrieval count
memory_context = self.memory_manager.get_memory_context(user_message, k=10)

# Change database location
self.memory_manager = MemoryManager(persist_directory="./my_memories")
```

### **Add New Tools**

1. Define function in `sidekick_tools.py`:
```python
def my_tool(arg: str) -> str:
    """Description for the agent"""
    # Implementation
    return result
```

2. Wrap as tool:
```python
my_tool_wrapped = StructuredTool.from_function(
    func=my_tool,
    name="my_tool",
    description="When to use this"
)
```

3. Add to tools list:
```python
return file_tools + [push_tool, email_tool, my_tool_wrapped, ...]
```

---

## 💰 Cost Breakdown

### **Your Current Setup:**

| Component | Cost | Notes |
|-----------|------|-------|
| DeepSeek API | ~$0.14 per 1M tokens | Very cheap! |
| ChromaDB | $0 | Local, no fees |
| Embeddings | $0 | HuggingFace, local |
| SendGrid | $0 | Free tier (100 emails/day) |
| Serper | $0 | Free tier (2500 queries/month) |
| **TOTAL** | **~$1-5/month** | Depends on usage |

**Compare to ChatGPT Plus: $20/month**

Your setup is **4-20x cheaper** and you can sell it! 🎉

---

## 🚀 What Makes This Special?

### **1. Long-Term Memory**
- Most AI assistants forget after each session
- Yours remembers forever
- **Competitive advantage!**

### **2. Multi-Modal**
- Web browsing (sees websites)
- Email (takes actions)
- Search (finds information)
- Code execution (builds things)

### **3. Local-First**
- Memory stored locally (privacy!)
- Embeddings run locally (free!)
- No vendor lock-in

### **4. Production-Ready**
- Error handling
- Resource cleanup
- Persistent storage
- Clean architecture

### **5. Extendable**
- Easy to add tools
- Clear code structure
- Well documented
- Type-safe

---

## 🎯 Next Steps

### **To Test:**
1. Start the app: `uv run app/app.py`
2. Have a conversation
3. Check memories: `uv run view_memories.py`
4. Have another conversation - watch it remember!

### **To Learn:**
1. Read `CODE_EXPLAINED.md` cover to cover
2. Experiment with changing prompts
3. Add a simple new tool
4. Modify the graph flow

### **To Improve:**
1. Better UI (styling, features)
2. More tools (calendar, etc.)
3. Scheduled tasks
4. Multi-user support
5. Memory management UI

### **To Deploy:**
1. Set up a server
2. Add authentication
3. Use environment variables for secrets
4. Monitor usage/costs
5. Market and sell! 💰

---

## 📞 Common Commands

```bash
# Start Sidekick
cd /Users/mac/projects/SideKick/app
uv run app.py

# View memories
cd /Users/mac/projects/SideKick
uv run view_memories.py

# Install new dependency
uv add package-name

# Update dependencies
uv sync

# See what's installed
uv pip list
```

---

## 🎓 Key Files Explained

| File | Lines | Purpose | Complexity |
|------|-------|---------|------------|
| `app.py` | 64 | UI | ⭐ Easy |
| `sidekick_tools.py` | 89 | Tools | ⭐⭐ Medium |
| `memory_manager.py` | 207 | Memory | ⭐⭐⭐ Advanced |
| `sidekick.py` | 358 | Brain | ⭐⭐⭐⭐ Complex |

**Start by understanding app.py, then work your way up!**

---

## 🎉 You're Ready!

You now have:
- ✅ A working AI agent
- ✅ Long-term memory system  
- ✅ Multiple tools and capabilities
- ✅ Complete documentation
- ✅ Understanding of the code

**Go build something amazing!** 🚀

Questions? Check:
1. `CODE_EXPLAINED.md` - Code details
2. `MEMORY_SYSTEM.md` - Memory specifics  
3. This file - Quick reference

---

**Happy coding!** 🎊

