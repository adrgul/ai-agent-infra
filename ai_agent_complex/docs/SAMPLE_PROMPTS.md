# Sample Prompts - AI Agent Demo

This document contains sample prompts to test all features of the AI Agent application.

## 🌤️ Weather Tool

Test getting weather forecasts for different locations.

### By City Name
```
What's the weather in Budapest?
```
```
Can you tell me the weather forecast for New York?
```
```
How's the weather looking in Tokyo this week?
```

### By Coordinates
```
Get me the weather for coordinates 47.4979, 19.0402
```

---

## 🗺️ Geocoding Tool

Convert addresses to coordinates and vice versa.

### Address to Coordinates
```
Convert this address to coordinates: 1600 Amphitheatre Parkway, Mountain View, CA
```
```
What are the coordinates for Eiffel Tower, Paris?
```
```
Get me the latitude and longitude for Central Park, New York
```

### Reverse Geocoding (Coordinates to Address)
```
What's the address at coordinates 40.7128, -74.0060?
```
```
Tell me what's located at 51.5074, -0.1278
```

---

## 🌐 IP Geolocation Tool

Get location information from IP addresses.

### Public IP Lookup
```
Where is IP address 8.8.8.8 located?
```
```
Can you geolocate 1.1.1.1?
```
```
What's the location of IP 142.250.185.46?
```

### Current Location (using default)
```
Where am I based on my IP?
```

---

## 💱 Currency Exchange Tool

Get current and historical exchange rates.

### Current Exchange Rates
```
What's the exchange rate from USD to EUR?
```
```
Convert 100 USD to Japanese Yen
```
```
How much is 50 GBP in CHF?
```

### Historical Rates
```
What was the USD to EUR exchange rate on 2024-01-15?
```
```
Show me GBP to USD rate for December 1st, 2024
```

---

## ₿ Cryptocurrency Price Tool

Get current cryptocurrency prices.

### Bitcoin
```
What's the current Bitcoin price?
```
```
How much is BTC in EUR?
```

### Ethereum
```
Get me the Ethereum price in USD
```
```
What's ETH worth in GBP?
```

### Other Cryptocurrencies
```
What's the price of Cardano (ADA) in USD?
```
```
How much is Solana (SOL) in EUR?
```

---

## 📝 File Creation Tool

Create and save text files.

### Simple Text Files
```
Create a file called "notes.txt" with the content: "This is a test note from the AI agent"
```
```
Save this to a file named "todo.txt": "1. Buy groceries\n2. Call dentist\n3. Finish project"
```

### Structured Content
```
Create a JSON file called "config.json" with this data: {"api_url": "http://localhost:8000", "timeout": 30}
```

---

## 🔍 History Search Tool

Search through past conversation history.

### Search Previous Conversations
```
Search my conversation history for "weather"
```
```
Find previous discussions about cryptocurrency
```
```
What did we talk about regarding exchange rates?
```

---

## 🔗 Complex Multi-Tool Requests

Test the agent's ability to chain multiple tools together.

### Weather + Geocoding
```
I'm planning a trip to the Colosseum in Rome. Can you find its coordinates and tell me the weather there?
```
```
What's the weather at the coordinates of the Statue of Liberty?
```

### IP + Weather
```
Find my location from my IP and tell me the weather here
```

### Geocoding + File Creation
```
Get the coordinates for Times Square and save them to a file called "locations.txt"
```

### Currency + Crypto Comparison
```
If I have 1000 USD, how much is that in EUR, and how much Bitcoin could I buy?
```

### Multi-step Planning
```
I need to:
1. Check the weather in London
2. Get the GBP to USD exchange rate
3. Find the coordinates of Big Ben
4. Save all this information to a file called "london-trip.txt"
```

---

## 💬 Conversational & Memory Tests

Test the agent's ability to maintain context.

### Follow-up Questions
```
User: What's the weather in Paris?
Agent: [responds with weather]
User: How about tomorrow?
```

```
User: What's the Bitcoin price?
Agent: [responds with price]
User: And Ethereum?
```

### Context Retention
```
User: Convert 500 USD to EUR
Agent: [responds with conversion]
User: Now convert that amount to GBP
```

```
User: Find the coordinates of Central Park
Agent: [responds with coordinates]
User: Get me the weather for those coordinates
```

---

## 🐛 Edge Cases & Error Handling

Test how the agent handles unusual inputs.

### Invalid Inputs
```
What's the weather on Mars?
```
```
Convert XYZ currency to ABC
```
```
Get me the price of a non-existent cryptocurrency: FAKECOIN
```

### Ambiguous Requests
```
Weather
```
```
Find it
```
```
How much?
```

---

## 🎯 Recommended Testing Sequence

1. **Start Simple**: Test individual tools with clear, specific requests
2. **Add Complexity**: Try multi-tool requests that require chaining
3. **Test Context**: Use follow-up questions to test memory
4. **Push Boundaries**: Try edge cases and error scenarios
5. **Verify History**: Use the search tool to find previous interactions

---

## 📊 Expected Results

For each category, you should see:

- ✅ Tool execution logged in the debug panel
- ✅ Accurate data returned from external APIs
- ✅ Natural language responses from the AI
- ✅ Memory updates showing stored information
- ✅ Proper error messages for invalid inputs

---

## 🚀 Quick Start Test Script

Copy and paste these prompts one by one to test all major features:

1. `What's the weather in Budapest?`
2. `What's the Bitcoin price in USD?`
3. `Convert 100 EUR to USD`
4. `Where is IP address 8.8.8.8 located?`
5. `Get coordinates for Eiffel Tower, Paris`
6. `Create a file called "test.txt" with content: "Hello from AI Agent"`
7. `Search my history for "weather"`

---

**Enjoy testing your AI Agent! 🤖**
