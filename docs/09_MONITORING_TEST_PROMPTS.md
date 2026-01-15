# Monitoring Test Prompts

Sample prompts to test and populate Grafana dashboards with metrics.

---

## 1. Basic LLM Metrics (LLM Dashboard)
**Tests**: inference count, tokens, latency, and cost

```
What is artificial intelligence?
```

```
Explain machine learning in simple terms.
```

```
Write a short poem about coding.
```

---

## 2. Tool Invocation Metrics (Agent Workflow Dashboard)
**Tests**: tool_invocation_count

```
What's the weather in Budapest?
```

```
What's the current price of Bitcoin?
```

```
What are the exchange rates for EUR to USD?
```

```
What's the weather in London and the current Bitcoin price?
```

---

## 3. Multiple Tool Calls (High Activity)
**Tests**: node latency and tool counts

```
I need to know: 1) Weather in New York, 2) Bitcoin price, 3) EUR/USD exchange rate, and 4) create a file called test.txt with this information.
```

```
Get weather for Paris, Tokyo, and Sydney. Also tell me the Ethereum price.
```

---

## 4. File Creation (Tool Metrics)
**Tests**: create_file tool

```
Create a file called "monitoring_test.txt" with the content: "This is a test of the monitoring system on January 14, 2026."
```

```
Save a shopping list to shopping.txt with: milk, eggs, bread, coffee
```

---

## 5. Complex Multi-Step Workflows (Agent Latency)
**Tests**: agent_execution_latency_seconds

```
First, get the weather in San Francisco. Then, if it's rainy, create a file called weather_report.txt with the weather details. If it's sunny, just tell me about outdoor activities.
```

```
Compare the weather in three cities: Berlin, Madrid, and Rome. Then create a summary file.
```

---

## 6. Search History (History Tool)
**Tests**: search_history tool

```
What did we talk about earlier?
```

```
Search our conversation history for weather
```

---

## 7. Rapid Fire (High Volume Testing)
**Tests**: Generate multiple requests quickly

```
Quick fact about Python programming
```

```
What's 125 * 47?
```

```
Tell me a tech joke
```

```
What year was JavaScript created?
```

---

## 8. Long Response (High Token Count)
**Tests**: token output metrics

```
Write a detailed 500-word article about the importance of observability in AI systems, including metrics, monitoring, and best practices.
```

```
Explain the entire history of computer programming from the 1950s to today in detail.
```

---

## 9. Error Scenarios (Error Metrics)
**Tests**: error tracking

```
Get weather for invalid-city-name-12345
```

```
Create a file with an extremely long name that might cause issues: /../../../../etc/passwd
```

---

## 10. Cost Intensive (Cost Dashboard)
**Tests**: Generate higher costs with complex requests

```
Analyze the pros and cons of 10 different programming languages (Python, JavaScript, Java, C++, Go, Rust, TypeScript, Ruby, PHP, Swift) in detail, covering syntax, performance, use cases, and ecosystem.
```

```
Write a comprehensive guide to AI agent architecture, covering prompt engineering, tool usage, memory management, error handling, observability, and deployment strategies. Include code examples.
```

---

## 📊 How to Monitor in Grafana

### After sending prompts:

1. **Open Grafana**: http://localhost:3001 (admin/admin)

2. **Navigate to**: Dashboards → AI Agent folder

3. **Select a dashboard**:
   - LLM Dashboard
   - Agent Workflow Dashboard
   - RAG Dashboard
   - Cost Dashboard

### Expected Metrics to Observe:

#### LLM Dashboard
- ✅ Inference count increases
- ✅ Token usage (input/output) shows activity
- ✅ Cost accumulates in USD
- ✅ Latency percentiles (p50/p95/p99) display
- ✅ Error rate (if any errors occur)

#### Agent Workflow Dashboard
- ✅ Agent execution count rises
- ✅ Tool invocation bars grow (weather, crypto, fx_rates, etc.)
- ✅ Node latency shows for agent_decide, tool_execution nodes
- ✅ Model fallback count (if fallbacks occur)

#### Cost Dashboard
- ✅ Cost per model increases
- ✅ Total cost gauge updates
- ✅ Cost per workflow shows average
- ✅ Daily burn rate accumulates

#### RAG Dashboard
(Will show activity if RAG features are used)
- ✅ Retrieval latency
- ✅ Relevance scores
- ✅ Vector DB query load
- ✅ Embedding generation count

---

## 🎯 Quick Test Sequence

Run these prompts in order for comprehensive testing:

1. `What's the weather in Budapest?` ← Basic tool call
2. `What's the Bitcoin price?` ← Another tool
3. `Create a file test.txt with: Hello World` ← File creation
4. `Weather in Paris and Bitcoin price` ← Multiple tools
5. `Write a 200-word essay on AI` ← High token output
6. Run 5 rapid simple queries ← Volume testing
7. Check all 4 Grafana dashboards ← Verify metrics

---

## 🔍 Prometheus Query Examples

If you want to query metrics directly:

```promql
# Total LLM calls
sum(llm_inference_count)

# Cost in last hour
increase(llm_cost_total_usd[1h])

# Tool usage
sum by (tool) (tool_invocation_count)

# Agent p95 latency
histogram_quantile(0.95, rate(agent_execution_latency_seconds_bucket[5m]))
```

Access Prometheus: http://localhost:9090

---

## ✅ Success Criteria

After running these prompts, you should see:

- [ ] LLM inference count > 10
- [ ] Multiple tools invoked (weather, crypto, create_file)
- [ ] Cost metrics showing non-zero values
- [ ] Latency histograms populated
- [ ] No critical errors (some test errors expected)
- [ ] All 4 Grafana dashboards showing data

---

**Last Updated**: January 14, 2026  
**Purpose**: Testing monitoring implementation from `docs/09_MONITORING_PROMPT.md`
