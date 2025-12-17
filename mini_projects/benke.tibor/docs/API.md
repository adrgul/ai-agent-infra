# KnowledgeRouter API Documentation

**Version:** 2.0  
**Base URL:** `http://localhost:8001/api/`  
**Content-Type:** `application/json`

---

## 📋 Table of Contents

- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [POST /api/query/](#post-apiquery)
  - [GET /api/sessions/{session_id}/](#get-apisessionssession_id)
  - [POST /api/reset-context/](#post-apireset-context)
  - [GET /api/usage-stats/](#get-apiusage-stats)
  - [DELETE /api/usage-stats/](#delete-apiusage-stats)
  - [GET /api/google-drive/files/](#get-apigoogle-drivefiles)
- [Data Models](#data-models)
- [Status Codes](#status-codes)
- [Rate Limits & Retry](#rate-limits--retry)

---

## 🔐 Authentication

Jelenleg nincs authentication (development mode). Production környezetben ajánlott:
- API Key authentication (Header: `X-API-Key`)
- JWT tokens session-alapú auth-hoz
- OAuth 2.0 enterprise integrációhoz

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Error Codes

| HTTP Code | Error Code | Jelentés |
|-----------|------------|----------|
| 400 | `INVALID_REQUEST` | Hibás request paraméterek |
| 400 | `EMPTY_QUERY` | Üres query string |
| 404 | `SESSION_NOT_FOUND` | Session nem létezik |
| 413 | `QUERY_TOO_LONG` | Query meghaladja a token limitet |
| 500 | `INTERNAL_ERROR` | Backend hiba |
| 503 | `SERVICE_UNAVAILABLE` | OpenAI API nem elérhető |

---

## 📡 Endpoints

### POST `/api/query/`

**Multi-domain RAG query feldolgozás LangGraph agent orchestrációval.**

Feldolgoz egy felhasználói kérdést, detektálja a domain-t (HR, IT, Finance, Marketing, Legal, General), releváns dokumentumokat keres Qdrant-ból domain-specifikus szűréssel, és GPT-4o-mini segítségével generál választ.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "user_id": "string",
  "session_id": "string",
  "query": "string",
  "organisation": "string (optional)"
}
```

**Parameters:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `user_id` | string | Yes | Felhasználó egyedi azonosítója | `"emp_001"` |
| `session_id` | string | Yes | Session azonosító (conversation tracking) | `"session_abc123"` |
| `query` | string | Yes | Felhasználó kérdése (max 10,000 tokens) | `"Mi a brand guideline sorhossz?"` |
| `organisation` | string | No | Szervezet neve (optional metadata) | `"ACME Corp"` |

**Constraints:**
- `query` nem lehet üres
- `query` max 10,000 tokens (~40,000 characters)
- `session_id` formátum: alphanumeric + underscore

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "domain": "marketing",
    "answer": "A brand guideline sorhosszra vonatkozó javaslat:\n\n### Maximális sorhossz\n- **70-80 karakter** a javasolt maximális érték\n- Megfelelő mennyiségű üres tér alkalmazása kötelező",
    "citations": [
      {
        "doc_id": "1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv#chunk2",
        "title": "Aurora_Digital_Brand_Guidelines_eng.docx",
        "score": 0.89,
        "url": null,
        "content": "Maximális sorhossz: 70–80 karakter..."
      }
    ],
    "workflow": {
      "action": "marketing_info_provided",
      "type": "information_query",
      "status": "completed",
      "next_step": null
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Request sikerességét jelzi |
| `data.domain` | string | Detektált domain (`hr`, `it`, `finance`, `legal`, `marketing`, `general`) |
| `data.answer` | string | Generált válasz (Markdown formátumban) |
| `data.citations` | array | Forrás dokumentumok listája |
| `data.citations[].doc_id` | string | Dokumentum egyedi azonosítója |
| `data.citations[].title` | string | Dokumentum címe/fájlneve |
| `data.citations[].score` | float | Relevancia score (0.0-1.0) |
| `data.citations[].url` | string\|null | Google Drive link (ha elérhető) |
| `data.citations[].content` | string | Chunk szöveg tartalma |
| `data.workflow` | object\|null | Workflow információk (ha triggerlődött) |
| `data.workflow.action` | string | Workflow action név |
| `data.workflow.type` | string | Workflow típus |
| `data.workflow.status` | string | Workflow státusz (`draft`, `pending`, `completed`) |
| `data.workflow.next_step` | string\|null | Következő lépés leírása |

**Error Responses:**

**400 Bad Request - Empty Query:**
```json
{
  "success": false,
  "error": "Query cannot be empty",
  "code": "EMPTY_QUERY"
}
```

**413 Request Too Large:**
```json
{
  "success": false,
  "error": "Query is too long. Please shorten your question to under 10,000 tokens (~40,000 characters).",
  "code": "QUERY_TOO_LONG",
  "details": {
    "estimated_tokens": 13500,
    "max_tokens": 10000
  }
}
```

**503 Service Unavailable:**
```json
{
  "success": false,
  "error": "OpenAI API is currently unavailable. Please try again later.",
  "code": "SERVICE_UNAVAILABLE"
}
```

#### Example Usage

**cURL:**
```bash
curl -X POST http://localhost:8001/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "emp_001",
    "session_id": "session_12345",
    "query": "Mi a brand guideline sorhossz ajánlása?"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8001/api/query/",
    json={
        "user_id": "emp_001",
        "session_id": "session_12345",
        "query": "Mi a brand guideline sorhossz ajánlása?"
    }
)

data = response.json()
print(f"Domain: {data['data']['domain']}")
print(f"Answer: {data['data']['answer']}")
print(f"Citations: {len(data['data']['citations'])}")
```

**PowerShell:**
```powershell
$body = @{
    user_id = "emp_001"
    session_id = "session_12345"
    query = "Mi a brand guideline sorhossz?"
} | ConvertTo-Json

$response = Invoke-WebRequest `
  -Uri "http://localhost:8001/api/query/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

$data = ($response.Content | ConvertFrom-Json).data
Write-Host "Domain: $($data.domain)"
Write-Host "Answer: $($data.answer)"
```

---

### GET `/api/sessions/{session_id}/`

**Session conversation history lekérdezése.**

Visszaadja egy session összes üzenetét időrendi sorrendben.

#### Request

**URL Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session egyedi azonosítója |

**Example:**
```
GET /api/sessions/session_abc123/
```

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "session_id": "session_abc123",
    "created_at": "2025-12-16T10:30:00Z",
    "updated_at": "2025-12-16T14:45:00Z",
    "message_count": 4,
    "messages": [
      {
        "role": "user",
        "content": "Mi a brand guideline sorhossz?",
        "timestamp": "2025-12-16T10:30:00Z"
      },
      {
        "role": "assistant",
        "content": "A brand guideline sorhosszra vonatkozó javaslat...",
        "timestamp": "2025-12-16T10:30:05Z",
        "citations": [
          {
            "doc_id": "...",
            "title": "Aurora_Digital_Brand_Guidelines_eng.docx",
            "score": 0.89
          }
        ]
      }
    ]
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "success": false,
  "error": "Session not found",
  "code": "SESSION_NOT_FOUND",
  "details": {
    "session_id": "session_abc123"
  }
}
```

#### Example Usage

**cURL:**
```bash
curl http://localhost:8001/api/sessions/session_abc123/
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8001/api/sessions/session_abc123/"
)

data = response.json()
print(f"Messages: {data['data']['message_count']}")
for msg in data['data']['messages']:
    print(f"{msg['role']}: {msg['content'][:50]}...")
```

---

### POST `/api/reset-context/`

**Session context törlése.**

Törli a session beszélgetési előzményeit, de a user profil megmarad.

#### Request

**Body:**
```json
{
  "session_id": "string"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | Törölni kívánt session ID |

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "message": "Context reset successfully",
  "data": {
    "session_id": "session_abc123",
    "cleared_messages": 12
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "success": false,
  "error": "Session not found",
  "code": "SESSION_NOT_FOUND"
}
```

#### Example Usage

**cURL:**
```bash
curl -X POST http://localhost:8001/api/reset-context/ \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_abc123"}'
```

---

### GET `/api/usage-stats/`

**OpenAI API token használat és költség tracking.**

Visszaadja az összes API hívás token használatát és költségét az utolsó reset óta.

#### Request

**No parameters required.**

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "data": {
    "calls": 127,
    "prompt_tokens": 45200,
    "completion_tokens": 12800,
    "total_tokens": 58000,
    "total_cost_usd": 0.0874,
    "average_tokens_per_call": 456.69,
    "models_used": {
      "gpt-4o-mini": {
        "calls": 127,
        "tokens": 58000,
        "cost_usd": 0.0874
      }
    }
  },
  "message": "Token usage statistics since last reset",
  "meta": {
    "last_reset": "2025-12-16T10:00:00Z",
    "tracking_duration_hours": 4.75
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `calls` | integer | Összes API hívás száma |
| `prompt_tokens` | integer | Input tokens összesen |
| `completion_tokens` | integer | Output tokens összesen |
| `total_tokens` | integer | Összes token (prompt + completion) |
| `total_cost_usd` | float | Becsült költség USD-ben (GPT-4o-mini pricing) |
| `average_tokens_per_call` | float | Átlagos token/hívás |

**Pricing (GPT-4o-mini per 1M tokens):**
- Input: $0.15
- Output: $0.60

#### Example Usage

**cURL:**
```bash
curl http://localhost:8001/api/usage-stats/
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8001/api/usage-stats/")
data = response.json()['data']

print(f"Total calls: {data['calls']}")
print(f"Total cost: ${data['total_cost_usd']:.4f}")
print(f"Avg tokens/call: {data['average_tokens_per_call']:.1f}")
```

---

### DELETE `/api/usage-stats/`

**Usage statistics nullázása.**

Visszaállítja a token tracking számláló(ka)t nullára.

#### Request

**No parameters required.**

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "message": "Usage statistics reset successfully",
  "data": {
    "previous_stats": {
      "calls": 127,
      "total_tokens": 58000,
      "total_cost_usd": 0.0874
    },
    "new_stats": {
      "calls": 0,
      "total_tokens": 0,
      "total_cost_usd": 0.0
    }
  }
}
```

#### Example Usage

**cURL:**
```bash
curl -X DELETE http://localhost:8001/api/usage-stats/
```

**Python:**
```python
import requests

response = requests.delete("http://localhost:8001/api/usage-stats/")
print(response.json()['message'])
```

---

### GET `/api/google-drive/files/`

**Google Drive marketing folder fájlok listázása.**

Visszaadja a marketing dokumentumokat tartalmazó Google Drive folder összes fájlját.

#### Request

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | string | No | `1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR` | Google Drive folder ID |

**Example:**
```
GET /api/google-drive/files/?folder_id=1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR
```

#### Response

**Success (200 OK):**

```json
{
  "success": true,
  "folder_id": "1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR",
  "file_count": 3,
  "files": [
    {
      "id": "150jnsbIl3HreheZyiCDU3fUt9cdL_EFS",
      "name": "Aurora_Digital_Arculati_Kezikonyv_HU.pdf",
      "mimeType": "application/pdf",
      "size": "163689",
      "createdTime": "2025-12-16T13:59:26.841Z",
      "modifiedTime": "2025-12-16T13:58:59.000Z",
      "webViewLink": "https://drive.google.com/file/d/150jnsbIl3HreheZyiCDU3fUt9cdL_EFS/view?usp=drivesdk",
      "thumbnailLink": "https://lh3.googleusercontent.com/...",
      "iconLink": "https://drive-thirdparty.googleusercontent.com/..."
    },
    {
      "id": "1utetoO-ApR4lmOpY1HS63va_gqmjDfsA",
      "name": "Aurora_Digital_Arculati_Kezikonyv_HU.docx",
      "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": "38007",
      "createdTime": "2025-12-16T13:59:26.702Z",
      "modifiedTime": "2025-12-16T13:58:36.000Z",
      "webViewLink": "https://docs.google.com/document/d/1utetoO-ApR4lmOpY1HS63va_gqmjDfsA/edit?usp=drivesdk"
    },
    {
      "id": "1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv",
      "name": "Aurora_Digital_Brand_Guidelines_eng.docx",
      "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": "37820",
      "createdTime": "2025-12-16T13:56:46.664Z",
      "modifiedTime": "2025-12-16T13:55:28.000Z",
      "webViewLink": "https://docs.google.com/document/d/1ACEdQxgUuAsDHKPBqKyp2kt88DjfXjhv/edit?usp=drivesdk"
    }
  ]
}
```

**Error Responses:**

**503 Service Unavailable:**
```json
{
  "success": false,
  "error": "Google Drive API is not available",
  "code": "SERVICE_UNAVAILABLE"
}
```

#### Example Usage

**cURL:**
```bash
curl "http://localhost:8001/api/google-drive/files/"
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8001/api/google-drive/files/")
data = response.json()

print(f"Total files: {data['file_count']}")
for file in data['files']:
    print(f"- {file['name']} ({file['mimeType']})")
```

---

## 📊 Data Models

### Citation

```typescript
interface Citation {
  doc_id: string;          // Unique document/chunk ID
  title: string;           // Document title/filename
  score: number;           // Relevance score (0.0-1.0)
  url: string | null;      // Google Drive link (optional)
  content: string;         // Chunk text content
}
```

### Workflow

```typescript
interface Workflow {
  action: string;          // Workflow action name
  type: string;            // Workflow type (vacation_request, ticket, etc.)
  status: string;          // Status (draft, pending, completed)
  next_step: string | null; // Next step description
}
```

### Message

```typescript
interface Message {
  role: "user" | "assistant"; // Message sender
  content: string;            // Message text
  timestamp: string;          // ISO 8601 timestamp
  citations?: Citation[];     // Citations (assistant only)
  workflow?: Workflow;        // Workflow info (assistant only)
}
```

### Session

```typescript
interface Session {
  session_id: string;
  created_at: string;       // ISO 8601 timestamp
  updated_at: string;       // ISO 8601 timestamp
  message_count: number;
  messages: Message[];
}
```

---

## 🚦 Status Codes

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| **200** | OK | Request successful | Successful query, session fetch |
| **201** | Created | Resource created | (Future: file upload) |
| **400** | Bad Request | Invalid parameters | Empty query, malformed JSON |
| **401** | Unauthorized | Missing/invalid auth | (Future: API key auth) |
| **404** | Not Found | Resource not exists | Session not found, file not found |
| **413** | Request Too Large | Payload too big | Query >10k tokens |
| **429** | Too Many Requests | Rate limit exceeded | (Future: rate limiting) |
| **500** | Internal Server Error | Backend exception | Unhandled error |
| **503** | Service Unavailable | External service down | OpenAI API timeout/error |

---

## 🔄 Rate Limits & Retry

### Automatic Retry Logic

A rendszer automatikus retry-t alkalmaz az alábbi esetekben:

**Retry Stratégia:**

```python
@retry_with_exponential_backoff(
    max_retries=3,
    initial_delay=1.0,
    exponential_base=2.0,
    jitter=True
)
```

**Retry Táblázat:**

| Error Type | Retry? | Backoff | Max Attempts |
|------------|--------|---------|--------------|
| RateLimitError (429) | ✅ Yes | Exponential (1s, 2s, 4s) | 3 |
| APITimeoutError | ✅ Yes | Exponential | 3 |
| APIConnectionError | ✅ Yes | Exponential | 3 |
| Server Error (5xx) | ✅ Yes | Exponential | 3 |
| Client Error (4xx) | ❌ No | - | 1 (immediate fail) |
| AuthenticationError | ❌ No | - | 1 (immediate fail) |

**Exponential Backoff Formula:**
```
delay = initial_delay * (exponential_base ^ attempt) * jitter
jitter = random(0.5, 1.5)  # 50-150% of base delay

# Examples:
Attempt 1: 1.0s * 2^0 * 1.2 = 1.2s
Attempt 2: 1.0s * 2^1 * 0.8 = 1.6s
Attempt 3: 1.0s * 2^2 * 1.3 = 5.2s
```

**Retry-After Header Support:**

RateLimitError esetén a rendszer tiszteletben tartja az OpenAI `Retry-After` headerét:

```python
if retry_after := error.retry_after:
    wait_time = float(retry_after)
else:
    wait_time = exponential_backoff(attempt)
```

### Rate Limits (OpenAI API)

**GPT-4o-mini (default model):**
- **TPM**: 200,000 tokens/minute
- **RPM**: 500 requests/minute
- **TPD**: 2,000,000 tokens/day

**Védelem:**
- Input validation: Max 10k tokens/query
- Prompt truncation: Max 100k tokens context
- Auto-retry with backoff

---

## 📝 Notes

### Multi-Domain Architecture

A rendszer egyetlen Qdrant collection-t használ (`multi_domain_kb`) domain-specifikus szűréssel:

```python
# Domain filter példa
domain_filter = Filter(
    must=[
        FieldCondition(
            key="domain",
            match=MatchValue(value="marketing")
        )
    ]
)

# Keresés domain filter-rel
results = qdrant_client.search(
    collection_name="multi_domain_kb",
    query_vector=embedding,
    query_filter=domain_filter,  # Csak marketing docs!
    limit=5
)
```

**Előnyök:**
- ✅ Skálázható több domain-re
- ✅ Gyors domain filtering (payload index)
- ✅ Egyetlen collection management
- ✅ Hybrid search ready (semantic + BM25)

### Token Estimation

**Approximation formula:**
```python
def estimate_tokens(text: str) -> int:
    return len(text) // 4  # 1 token ≈ 4 chars
```

**Accuracy:**
- English: ~90% accurate
- Hungarian: ~85% accurate (longer words)
- Code: ~70% accurate (special chars)

**Production recommendation:**
```python
from tiktoken import encoding_for_model

enc = encoding_for_model("gpt-4o-mini")
tokens = len(enc.encode(text))  # Exact token count
```

### Cost Optimization Tips

**1. Input Validation:**
```python
# Block oversized queries early
check_token_limit(query, max_tokens=10000)
# Saves: ~$0.015 per rejected 100k char query
```

**2. Prompt Truncation:**
```python
# Use top 3 docs only, truncate rest
if len(context) > 100000:
    context = top_3_docs_full + rest_truncated
# Saves: ~30% token cost
```

**3. Caching (Future):**
```python
# Cache embeddings for frequently queried docs
# Saves: $0.02 per 1M cached tokens
```

---

## 🔗 Related Documentation

- [Main README](../README.md)
- [Installation Guide](../INSTALLATION.md)
- [Error Handling Architecture](ERROR_HANDLING.md) (coming soon)
- [Google Drive Setup](GOOGLE_DRIVE_SETUP.md)

---

**Last Updated:** December 17, 2025  
**Maintained by:** KnowledgeRouter Team
