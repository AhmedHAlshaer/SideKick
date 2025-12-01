# Google Sheets Output Example

## What Your Spreadsheet Will Look Like

After conversations with your Sidekick agent, your Google Sheet will contain detailed logs like this:

### Conversations Worksheet

| Timestamp | Session ID | User Message | Assistant Response | Success Criteria | Tools Used | Conversation Status | Success Met | User Input Needed | Memories Extracted | Response Length | Turn Number | Date | Time | Duration (seconds) |
|-----------|-----------|--------------|-------------------|-----------------|------------|-------------------|-------------|------------------|-------------------|----------------|-------------|------|------|-------------------|
| 2024-11-27T14:23:45.123456 | 550e8400-e29b-41d4 | What's the weather in New York? | Let me check the weather for New York... [full response] | Provide accurate weather info | browser_navigate, browser_snapshot | completed | Yes | No | ["User interested in NY weather"] | 245 | 1 | 2024-11-27 | 14:23:45 | 3.45 |
| 2024-11-27T14:25:12.654321 | 550e8400-e29b-41d4 | Thanks! What about tomorrow? | Based on the forecast... [full response] | Provide accurate weather info | browser_navigate | completed | Yes | No | [] | 182 | 2 | 2024-11-27 | 14:25:12 | 2.11 |
| 2024-11-27T14:30:00.111111 | 661f9511-f3ac-52e5 | Write a Python function to calculate fibonacci | Here's a fibonacci function... [code and explanation] | Code should be correct and efficient | execute_code | completed | Yes | No | ["User codes in Python"] | 456 | 1 | 2024-11-27 | 14:30:00 | 1.87 |
| 2024-11-27T15:10:22.222222 | 772fa622-g4bd-63f6 | Can you help me book a flight? | I can help you search for flights, but I'll need more information... | Help with flight booking | None | completed | No | Yes | ["User travels frequently"] | 198 | 1 | 2024-11-27 | 15:10:22 | 0.95 |

### Summary Worksheet (Auto-generated)

The system also creates a Summary worksheet with automatic statistics:

| Metric | Value |
|--------|-------|
| **Total Conversations** | 234 |
| **Success Rate** | 87.5% |
| **Average Response Length** | 312 characters |
| **Average Duration** | 2.34 seconds |
| **Most Used Tool** | browser_navigate |
| **Total Sessions** | 156 |

## Real-World Examples

### Example 1: Research Task

```
User Message: "Find the latest news about AI regulations"
Assistant Response: "I'll search for recent AI regulation news... [detailed findings with sources]"
Success Criteria: "Find recent, credible news sources"
Tools Used: browser_navigate, browser_snapshot
Status: completed
Success Met: Yes
Duration: 8.2 seconds
```

### Example 2: Coding Help

```
User Message: "Debug my Python script that's throwing an error"
Assistant Response: "Let me analyze your code... [analysis and fix]"
Success Criteria: "Identify and fix the error"
Tools Used: execute_code
Status: completed
Success Met: Yes
Duration: 2.1 seconds
```

### Example 3: Information Gathering

```
User Message: "What are the top 5 Python frameworks for web development?"
Assistant Response: "Here are the top 5 Python web frameworks... [detailed comparison]"
Success Criteria: "Provide accurate, current information"
Tools Used: None (used existing knowledge)
Status: completed
Success Met: Yes
Duration: 1.3 seconds
```

## Analytics You Can Do

### 1. Success Analysis
Filter by "Success Met" = "Yes" to see your success rate over time.

### 2. Tool Usage Patterns
Sort by "Tools Used" to see which tools are most frequently called.

### 3. Response Time Trends
Use the "Duration" column to create charts showing response times over time.

### 4. Topic Analysis
Search in "User Message" column to find all conversations about specific topics.

### 5. Session Analysis
Group by "Session ID" to see multi-turn conversations.

### 6. Memory Insights
Look at "Memories Extracted" to see what the agent is learning about users.

## Exporting and Analyzing

### Export to CSV
1. File → Download → Comma-separated values (.csv)
2. Open in Excel, R, Python, or any data analysis tool

### Create Visualizations
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('sidekick_conversations.csv')

# Success rate over time
df['Date'] = pd.to_datetime(df['Date'])
success_rate = df.groupby('Date')['Success Met'].apply(
    lambda x: (x == 'Yes').sum() / len(x) * 100
)
success_rate.plot(kind='line', title='Success Rate Over Time')
plt.ylabel('Success Rate (%)')
plt.show()

# Tool usage
tools = df['Tools Used'].str.split(', ').explode()
tools.value_counts().head(10).plot(kind='bar', title='Top 10 Most Used Tools')
plt.show()

# Response time distribution
df['Duration (seconds)'].hist(bins=50)
plt.title('Response Time Distribution')
plt.xlabel('Duration (seconds)')
plt.show()
```

### Google Data Studio Dashboard
Connect your Google Sheet to Google Data Studio for real-time dashboards:
1. Go to [Google Data Studio](https://datastudio.google.com/)
2. Create → Data Source → Google Sheets
3. Select your Sidekick Conversations sheet
4. Create visualizations and dashboards

## Privacy & Security

### What's Logged
- ✅ All messages (user and assistant)
- ✅ Tools used
- ✅ Timestamps and metadata
- ✅ Success indicators

### What's NOT Logged
- ❌ API keys or credentials
- ❌ Browser session data
- ❌ Internal system states

### Security Best Practices
1. **Restrict Sheet Access** - Only share with team members who need it
2. **Regular Backups** - Export to CSV periodically
3. **Monitor Access** - Check Google Sheet's version history
4. **Rotate Credentials** - Update service account keys every 90 days

## Tips for Analysis

### 1. Use Filters
Create filter views for:
- Successful vs. unsuccessful conversations
- Conversations by date range
- Conversations using specific tools
- Sessions requiring user input

### 2. Create Pivot Tables
Analyze patterns with pivot tables:
- Success rate by hour of day
- Average duration by tool used
- Most common user queries

### 3. Conditional Formatting
Highlight important data:
- Red for "Success Met" = "No"
- Green for duration < 2 seconds
- Yellow for "User Input Needed" = "Yes"

### 4. Use Google Sheets Functions
```
# Count successful conversations today
=COUNTIFS(Conversations!M:M, TODAY(), Conversations!H:H, "Yes")

# Average response time this week
=AVERAGEIF(Conversations!M:M, ">="&TODAY()-7, Conversations!O:O)

# Most used tool
=INDEX(Conversations!F:F, MODE(MATCH(Conversations!F:F, Conversations!F:F, 0)))
```

## Next Steps

1. ✅ Set up Google Sheets integration
2. ✅ Run a few test conversations
3. ✅ Explore your data in the sheet
4. 📊 Create your first analysis
5. 🎯 Set up automated reporting
6. 🚀 Build custom dashboards

Happy analyzing! 📊✨

