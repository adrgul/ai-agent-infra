# Multi-Step Workflow Test Prompt

This document contains the comprehensive test prompt for validating the agent's multi-step workflow capabilities.

## 🎯 Full Test Prompt

Copy and paste this entire prompt to test all 5 tools in a single request:

```
Hi! I'm Maria from Budapest. Can you help me with these tasks:

1. Tell me tomorrow's weather forecast
2. Show me how much 500 EUR is in HUF
3. Find the current Bitcoin price
4. Search my conversation history for "weather"
5. Save a summary of all this information to a file called "summary.txt"
```

## ✅ Expected Results

When this prompt is executed successfully, you should see:

### Tools Used (in Debug Panel):
1. ✅ **weather** - Get tomorrow's weather forecast
2. ✅ **fx_rates** - Convert 500 EUR to HUF
3. ✅ **crypto_price** - Get Bitcoin price in USD
4. ✅ **search_history** - Search for "weather" in past conversations
5. ✅ **create_file** - Save summary to `summary.txt`

### Memory Updates:
- User name extracted: "Maria"
- Default city updated: "Budapest"
- Preferences stored in user profile

### Final Response:
The agent should provide a comprehensive response that includes:
- Tomorrow's weather forecast with temperatures
- EUR to HUF exchange rate and conversion result
- Current Bitcoin price
- Results from history search (if any previous weather queries exist)
- Confirmation that summary was saved to file

### File Created:
- Location: `backend/data/files/user_<USER_ID>/summary.txt`
- Content: Summary of all the information gathered from the 5 tool executions

## 🔧 Technical Details

### Workflow Architecture:
```
Entry → agent_decide → tool_weather → agent_decide → tool_fx_rates → agent_decide → tool_crypto_price → agent_decide → tool_search_history → agent_decide → tool_create_file → agent_decide → agent_finalize → END
```

### Safety Limits:
- **Max Iterations**: 10 tool calls (set in `MAX_ITERATIONS` constant)
- **LangGraph Recursion Limit**: 50 (set in `workflow.compile(recursion_limit=50)`)
- **Timeout**: None (runs until completion or limit reached)

### Iteration Tracking:
- Each tool call increments `iteration_count` in `AgentState`
- If `iteration_count >= MAX_ITERATIONS`, workflow forces finalization
- Prevents infinite loops while allowing complex multi-step workflows

## 🐛 Troubleshooting

### If you see "Recursion limit reached" error:
- The LangGraph recursion limit (50) was hit
- This means the agent attempted more than 50 state transitions
- Check logs for infinite loop patterns
- May need to adjust prompts or increase `recursion_limit`

### If only 1 tool executes:
- Check that backend was rebuilt after latest changes
- Verify `workflow.add_edge(f"tool_{tool_name}", "agent_decide")` is present
- Confirm decision prompt includes multi-task instructions

### If MAX_ITERATIONS warning appears:
- Agent hit 10 tool call limit
- Check if agent is calling same tool repeatedly
- May need to adjust decision prompt for better task completion detection

## 📊 Monitoring

### Backend Logs to Watch:
```bash
docker-compose logs -f backend
```

Look for:
- `Agent decision: {"action": "call_tool", "tool_name": "...", ...}`
- `Tool executed: <tool_name>`
- `Max iterations (10) reached, forcing finalize` (if limit hit)
- `Agent run completed`

### Debug Panel in Frontend:
- **Tools used**: Should show 5 entries
- **Memory Snapshot**: Should show name "Maria" and city "Budapest"
- **Conversation**: Should show all tool results integrated into response

## 🚀 Alternative Test Prompts

### Simpler 3-Tool Test:
```
Can you:
1. Check the weather in Paris
2. Convert 100 EUR to USD
3. Get the Ethereum price
```

### Complex 7-Tool Test:
```
I need you to:
1. Find my location from my IP
2. Get the weather for my location
3. Convert 1000 USD to EUR
4. Get Bitcoin price
5. Get Ethereum price
6. Search my history for "crypto"
7. Save all this info to "report.txt"
```

### Edge Case - Repeated Tool:
```
Can you:
1. Get weather in London
2. Get weather in Paris
3. Get weather in Tokyo
```
(Tests if agent can call same tool multiple times)

---

**Last Updated**: December 8, 2025  
**Status**: Ready for testing after backend rebuild with recursion_limit=50
