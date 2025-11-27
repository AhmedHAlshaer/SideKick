# 🔍 How to View Your Sidekick's Memories

Quick guide to seeing what your Sidekick remembers!

---

## 🎮 Method 1: Interactive Memory Viewer

### **Run the viewer:**
```bash
cd /Users/mac/projects/SideKick
uv run view_memories.py
```

### **You'll see this menu:**
```
🧠 Sidekick Memory Viewer
==================================================

What would you like to do?
1. View all memories
2. Search for specific memories
3. Add a manual memory
4. Clear all memories (⚠️  dangerous!)
5. Get memory statistics
6. Exit

Enter choice (1-6):
```

### **Option 1: View All Memories**
Shows every memory stored:
```
1. User studies at Indiana University (IU)
   Type: fact
   Time: 2025-11-26T15:27:07.594178
   Source: Conversation about university

2. User prefers Python programming
   Type: preference
   Time: 2025-11-26T15:28:33.123456
```

### **Option 2: Search Memories**
Find specific memories:
```
What do you want to search for? university
How many results? (default 5): 3

✅ Found 3 relevant memories:

1. User studies at Indiana University (IU)
   Relevance Score: 0.918 (lower = more relevant)
   Type: fact

2. User's email ends with @iu.edu
   Relevance Score: 1.156
   Type: fact
```

### **Option 3: Add Memory**
Manually store information:
```
What should I remember? I prefer dark mode in all apps

Memory types:
1. fact (general information)
2. preference (user preferences)
3. instruction (how to do things)
4. other

Choose type (1-4, default 1): 2

✅ Memory stored successfully as 'preference'!
```

### **Option 5: Statistics**
See overview:
```
📊 MEMORY STATISTICS
==================================================

📈 Total Memories: 12

📁 Breakdown by Type:
   - fact: 7
   - preference: 3
   - instruction: 2

🕐 Most Recent Memory:
   User is excited about vector databases...
   Time: 2025-11-26T15:30:45.123456
```

---

## 🐍 Method 2: Python Script

### **Quick peek at memories:**

Create `peek_memory.py`:
```python
from app.memory_manager import MemoryManager

mm = MemoryManager()
memories = mm.recall_memories("everything", k=10)

print(f"Found {len(memories)} memories:\n")
for i, mem in enumerate(memories, 1):
    print(f"{i}. {mem['content']}")
```

Run it:
```bash
uv run peek_memory.py
```

---

## 📂 Method 3: Direct Database Inspection

### **Check if database exists:**
```bash
ls -la chroma_db/
```

Output:
```
drwxr-xr-x  chroma_db/
-rw-r--r--  chroma.sqlite3  # SQLite database
-rw-r--r--  [vector files]  # Embedding data
```

### **See database size:**
```bash
du -sh chroma_db/
```

Example output: `2.4M chroma_db/`

---

## 🧪 Test the Memory System

### **Full Test Flow:**

**Step 1: Start Sidekick**
```bash
cd /Users/mac/projects/SideKick/app
uv run app.py
```

**Step 2: Have a conversation**
```
Message: "I'm Ahmed, a student at Indiana University. I'm building an AI assistant called Sidekick. I love Python and I'm excited about vector databases!"

Success Criteria: "Tell me you understand"

[Let Sidekick respond]
```

**Step 3: Check what was remembered**
```bash
# In new terminal
cd /Users/mac/projects/SideKick
uv run view_memories.py
```

Choose option 1 (View all memories)

**You should see something like:**
```
1. User's name is Ahmed
   Type: fact

2. User studies at Indiana University
   Type: fact

3. User is building an AI assistant called Sidekick
   Type: fact

4. User prefers Python programming language
   Type: preference

5. User is excited about vector databases
   Type: preference
```

**Step 4: Test recall** (new conversation)
```
Message: "Help me with my AI project"
Success Criteria: "Provide relevant help"
```

Watch the terminal output - you'll see:
```
🧠 Recalled 5 relevant memories for: Help me with my AI project...
```

The response will be personalized based on what it remembers about you!

---

## 🎯 What Gets Remembered?

### **✅ Stored:**
- Your name and personal info
- Where you study/work
- Projects you're working on
- Programming language preferences
- Tools and technologies you use
- Communication style preferences
- Recurring patterns in requests

### **❌ Not Stored:**
- Temporary information (today's weather)
- One-time tasks (send this specific email)
- Sensitive data (unless you explicitly mention it)
- Obvious common knowledge

---

## 🔧 Customize Memory Behavior

### **Store More Context:**

Edit `sidekick.py`, in the `worker` method:
```python
# Change from 5 to 10 memories
memory_context = self.memory_manager.get_memory_context(
    user_message, 
    k=10  # Get more context
)
```

### **Change Memory Extraction:**

Edit `sidekick.py`, in the `memory_extractor` system message:
```python
system_message = """You are a memory extraction system...

Extract things like:
- User preferences
- Personal information  
- Projects
- YOUR NEW CATEGORIES HERE

Do NOT extract:
- YOUR EXCLUSIONS HERE
"""
```

### **Manual Memory Management:**

```python
from app.memory_manager import MemoryManager

mm = MemoryManager()

# Add memory
mm.store_memory(
    content="User prefers detailed explanations",
    memory_type="preference"
)

# Search
results = mm.recall_memories("how does user like explanations?", k=3)

# Clear all (careful!)
mm.clear_all_memories()
```

---

## 📊 Memory Analytics

### **See Memory Growth Over Time:**

Create `memory_analytics.py`:
```python
from app.memory_manager import MemoryManager
from collections import Counter
from datetime import datetime

mm = MemoryManager()
memories = mm.recall_memories("", k=1000)

# Count by type
types = Counter(m['metadata'].get('memory_type', 'unknown') 
                for m in memories)

# Count by date
dates = Counter(m['metadata'].get('timestamp', '')[:10] 
                for m in memories if 'timestamp' in m['metadata'])

print(f"Total Memories: {len(memories)}\n")
print("By Type:")
for mem_type, count in types.items():
    print(f"  {mem_type}: {count}")

print("\nBy Date:")
for date, count in sorted(dates.items()):
    print(f"  {date}: {count}")
```

---

## 🎓 Understanding the Output

### **Relevance Scores:**

```
1. User studies at IU
   Relevance Score: 0.918  ← Very relevant! (low = better)

2. User likes Python
   Relevance Score: 1.234  ← Somewhat relevant

3. Random fact
   Relevance Score: 2.567  ← Not very relevant
```

**Lower score = More relevant!**

This is the "distance" in vector space:
- 0.0 = Identical meaning
- < 1.0 = Very similar
- 1.0-2.0 = Related
- > 2.0 = Different topic

### **Timestamps:**

```
Time: 2025-11-26T15:27:07.594178
      YYYY-MM-DD HH:MM:SS.microseconds
```

ISO 8601 format - standard datetime format

---

## 🐛 Troubleshooting

### **"No memories found"**

**Cause:** Database is empty or query doesn't match

**Solution:**
```bash
# Check if database exists
ls chroma_db/

# If not, have a conversation with Sidekick first
# Then memories will be created automatically
```

### **"Module not found" error**

**Cause:** Dependencies not installed

**Solution:**
```bash
cd /Users/mac/projects/SideKick
uv sync
```

### **"Too many memories, slow search"**

**Cause:** Database growing large

**Solutions:**
1. Clear old memories periodically
2. Use more specific queries
3. Lower the `k` parameter

---

## 💡 Pro Tips

### **1. Regular Memory Review**
Check memories weekly:
```bash
uv run view_memories.py
# Option 1: View all
# Option 5: Statistics
```

### **2. Pre-populate Important Info**
Add key facts manually before first use:
```bash
uv run view_memories.py
# Option 3: Add memory
```

### **3. Export Memories**
Backup your knowledge base:
```python
from app.memory_manager import MemoryManager
import json

mm = MemoryManager()
memories = mm.recall_memories("", k=1000)

with open('memory_backup.json', 'w') as f:
    json.dump([{
        'content': m['content'],
        'metadata': m['metadata']
    } for m in memories], f, indent=2)
```

### **4. Search Tips**

**Good queries:**
- "What are my programming preferences?"
- "What projects am I working on?"
- "What does the user study?"

**Bad queries:**
- Single words: "python" (too vague)
- Too specific: "exact text from memory"

---

## 🎉 Summary

**To view memories, you have 3 methods:**

1. **Interactive Tool** (easiest): `uv run view_memories.py`
2. **Python Script** (programmatic): Create custom scripts
3. **Direct Database** (advanced): Check chroma_db/ folder

**The interactive tool is your best bet!** 🚀

---

**Now go check what your Sidekick remembers!** 🧠✨

