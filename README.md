# Bing Search Agent

An interactive AI research assistant powered by Azure AI Agents with mandatory Bing search capabilities. This agent provides accurate, well-sourced information by performing web searches for every query and maintaining complete audit trails of search compliance.

## 🚀 Features

- **Mandatory Web Search**: Agent is configured to perform Bing searches for every query
- **Interactive Conversation Mode**: Continuous chat interface until user types 'exit'
- **Structured JSON Responses**: Responses follow a standardized format with grounding metadata
- **Search Compliance Tracking**: Monitors and reports whether searches were performed
- **Comprehensive Logging**: Each conversation saved as timestamped markdown files
- **Citation Management**: Automatic extraction and display of source URLs and titles
- **Temperature Control**: Set to 0.1 for consistent, deterministic responses
- **Tool Choice Configuration**: Forces appropriate tool usage for search operations
- **Real-time Feedback**: Shows search status and source count during conversations

## 📁 Project Structure

```
bing-search-agent/
├── sample_agents_bing_grounding.py    # Main application script
├── agent_instructions.txt             # Comprehensive agent behavior instructions
├── requirements.txt                  # Python dependencies
├── search-results/                   # Directory for conversation logs
│   └── conversation_YYYYMMDD_HHMMSS.md  # Timestamped conversation files
└── README.md                         # This file
```

## 🛠️ Setup


### Development Container Setup

1. Open the project in VS Code
2. Install the "Dev Containers" extension if not already installed
3. Open the Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
4. Select "Dev Containers: Reopen in Container"
5. Wait for the container to build and start

### Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PROJECT_ENDPOINT` | Azure AI Project endpoint from Overview page | `https://your-project.cognitiveservices.azure.com/` |
| `MODEL_DEPLOYMENT_NAME` | AI model deployment name from Models + endpoints tab | `gpt-4o` |
| `AZURE_BING_CONNECTION_ID` | Full resource ID of your Bing connection | `/subscriptions/.../connections/bing-connection` |

## 🎯 Usage

### Interactive Mode

```bash
python sample_agents_bing_grounding.py
```

The agent will start in interactive mode:

```
🔍 Bing Search Agent - Interactive Mode
Type 'exit' to end the conversation and save results
==================================================
✅ Created agent, ID: asst_xxx
✅ Created thread, ID: thread_xxx

🧑 You: What is machine learning?

🤖 Agent is thinking and searching...
DEBUG: Tool call type: 'bing_grounding'
DEBUG: Stored tool call - ID: call_abc123, Type: bing_grounding

🤖 Agent (🔍 Search used):
[Agent's response with current information from web search]

🔍 Search queries used: machine learning definition, what is ML
📊 Sources found: 3

📚 Sources (3 found):
  1. Machine Learning Overview - MIT
     https://web.mit.edu/...
==================================================
```

### Response Format

The agent returns structured JSON responses:

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Your answer with current information..."
          }
        ],
        "role": "model"
      },
      "groundingMetadata": {
        "webSearchQueries": ["search term 1", "search term 2"],
        "groundingChunks": [
          {"web": {"uri": "https://source1.com", "title": "Source 1"}}
        ],
        "groundingSupports": [
          {
            "segment": {"startIndex": 0, "endIndex": 100, "text": "..."},
            "groundingChunkIndices": [0]
          }
        ]
      }
    }
  ]
}
```

## 📊 Conversation Logging

Each session creates a timestamped markdown file in `search-results/` with:

### Conversation Summary
- Total messages and agent runs
- Search compliance statistics
- Overall compliance status (✅ COMPLIANT / ❌ PARTIAL)

### Per-Exchange Details
- **Search Status**: Whether Bing search was used
- **User Input**: Original question
- **Agent Response**: Complete JSON response
- **Citations**: Extracted source URLs and titles
- **Technical Details**: Run IDs, thread IDs, tool call information

### Example Log Structure

```markdown
# Conversation Log - 2025-07-15 18:30:22

## Conversation Summary
- **Total Messages**: 3
- **Total Agent Runs**: 3
- **Runs with Bing Search**: 3/3
- **Total Search Calls**: 5
- **Overall Compliance**: ✅ COMPLIANT

## Exchange 1

### Search Status
- **Bing Search Used**: ✅ YES
- **Search Calls**: 2
- **Compliance**: COMPLIANT

### User Input
What is the weather today?

### Agent Response
[JSON response with grounding metadata]
```

## ⚙️ Configuration

### Agent Instructions

The `agent_instructions.txt` file contains comprehensive instructions including:

- **Mandatory Search Requirements**: Forces web search for every query
- **Source Quality Standards**: Guidelines for evaluating source reliability
- **Response Format Guidelines**: Structured approach to different query types
- **Grounding Metadata Usage**: How to leverage search result metadata
- **Citation Standards**: Requirements for proper source attribution

### Key Configuration Parameters

```python
# In sample_agents_bing_grounding.py
agent = agents_client.create_agent(
    model=os.environ["MODEL_DEPLOYMENT_NAME"],
    name="bing-search-agent",
    instructions=instructions,
    tools=bing.definitions,
    temperature=0.1,  # Low temperature for consistent responses
)

# Tool choice configuration
run = agents_client.runs.create_and_process(
    thread_id=thread.id, 
    agent_id=agent.id, 
    tool_choice={"type": "bing_grounding"}  # Forces search tool usage
)
```

## 🔍 Search Compliance Features

### Automatic Detection
- Monitors all tool calls for Bing search usage
- Tracks search call counts per exchange
- Reports compliance status in real-time

### Debug Information
- Shows tool call types during execution
- Displays search queries used
- Counts sources found per search

### Compliance Reporting
- Real-time status indicators (🔍 Search used / ⚠️ No search)
- Detailed statistics in conversation logs
- Session summary with overall compliance metrics

## 📈 Session Statistics

At the end of each session:

```
📊 Session Summary:
   • Total exchanges: 5
   • Exchanges with search: 5/5
   • Total search calls: 12
   • Compliance: ✅ FULL
```

## 🚀 Advanced Features

### Temperature Control
- Set to 0.1 for deterministic, consistent responses
- Reduces randomness in search behavior and formatting
- Improves compliance with structured response requirements

### Tool Choice Management
- Configured to prefer Bing grounding tools
- Ensures search tools are used appropriately
- Supports mandatory search workflow

### JSON Response Parsing
- Automatically extracts main content from structured responses
- Displays grounding metadata information
- Graceful fallback for non-JSON responses