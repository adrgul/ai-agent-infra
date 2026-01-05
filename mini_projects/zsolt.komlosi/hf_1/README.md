# SLA Advisor Agent

Ügyfélszolgálati SLA (Service Level Agreement) tanácsadó agent, amely segít meghatározni a support ticketek prioritását és válaszidejét.

## Projekt Leírás

Ez a mini-projekt egy AI agent, amely:
- Elemzi a beérkező support ticket szövegét
- Felismeri a nyelvet és a hangulatot (sentiment)
- Meghatározza a kategóriát és prioritást
- IP cím alapján lekérdezi az ügyfél lokációját és időzónáját
- Kiszámítja az SLA határidőt (munkaszüneti napok figyelembevételével)
- Javaslatot tesz a megfelelő support csapatra (routing)



| SLA Advisor | SupportAI Komponens |
|-------------|---------------------|
| Nyelv felismerés | Intent Detection |
| Hangulat elemzés | Triage - sentiment |
| Prioritás javaslat | Triage - priority |
| SLA számítás | Triage - sla_hours |
| Routing javaslat | Triage - suggested_team |
| Időzóna kezelés | SLA compliance |

## Használt API-k

### 1. ip-api.com
- **Cél:** IP geolokáció, időzóna meghatározás
- **Ingyenes:** Igen, API kulcs nélkül (45 request/perc limit)
- **Dokumentáció:** https://ip-api.com/docs

### 2. Nager.Date API
- **Cél:** Munkaszüneti napok lekérdezése
- **Ingyenes:** Igen, API kulcs nélkül
- **Dokumentáció:** https://date.nager.at/Api

## Telepítés és Indítás

### Előfeltételek
- Python 3.11+
- OpenAI API kulcs

### Lokális Futtatás

1. **Navigálj a projekt mappába:**
   ```bash
   cd mini_projects/zsolt.komlosi/ht_1
   ```

2. **Hozz létre virtuális környezetet (opcionális, de ajánlott):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Telepítsd a függőségeket:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Hozd létre a .env fájlt:**
   ```bash
   copy .env.example .env
   # vagy Linux/Mac:
   cp .env.example .env
   ```

5. **Add meg az OpenAI API kulcsot a .env fájlban:**
   ```
   OPENAI_API_KEY=sk-your-actual-api-key
   ```

6. **Indítsd a programot:**
   ```bash
   python main.py
   ```

### Docker Futtatás

1. **Hozd létre a .env fájlt:**
   ```bash
   copy .env.example .env
   ```

2. **Add meg az OpenAI API kulcsot a .env fájlban**

3. **Indítsd Docker-rel:**
   ```bash
   docker-compose run --rm sla-advisor
   ```

## Használat

A program indítása után egy interaktív chat felület jelenik meg. Írd be a support ticket szövegét, opcionálisan az IP címmel együtt:

```
Te: A számlámon dupla terhelés van! IP: 8.8.8.8
```

A program elemzi a ticketet és kiírja az eredményt.

**Kilépés:** `exit`, `quit`, `kilépés`, `q`

**Segítség:** `help`, `segítség`, `?`

---

## Teszt Esetek

Az alábbi előre elkészített teszt adatokkal tesztelhető a program:

### 1. Sürgős számlázási probléma (Német ügyfél)

**Input:**
```
Doppelte Abbuchung auf meiner Rechnung! Das ist unakzeptabel! IP: 85.214.132.117
```

**Elvárt eredmény:**
- Nyelv: Német
- Hangulat: Frusztrált
- Kategória: Számlázás - Dupla terhelés
- Prioritás: P1 vagy P2 (Sürgős)
- Routing: Finance Team

---

### 2. Általános kérdés (USA ügyfél)

**Input:**
```
How do I change my subscription plan? IP: 8.8.8.8
```

**Elvárt eredmény:**
- Nyelv: Angol
- Hangulat: Semleges
- Kategória: Előfizetés / Fiók
- Prioritás: P3 (Közepes)
- Routing: Sales Team vagy Account Team

---

### 3. Technikai hiba (Magyar ügyfél)

**Input:**
```
Nem tudok belépni a fiókba, hibaüzenetet kapok. IP: 84.0.64.1
```

**Elvárt eredmény:**
- Nyelv: Magyar
- Hangulat: Semleges vagy kissé frusztrált
- Kategória: Technikai - Bejelentkezési hiba
- Prioritás: P2 (Magas)
- Routing: IT Support

---

### 4. Sürgős rendszerhiba (UK ügyfél)

**Input:**
```
URGENT: Production system is down! We are losing money every minute! IP: 51.148.64.0
```

**Elvárt eredmény:**
- Nyelv: Angol
- Hangulat: Nagyon frusztrált / Sürgős
- Kategória: Technikai - Rendszerleállás
- Prioritás: P1 (Kritikus)
- Routing: IT Support (Eszkaláció)

---

### 5. Feature kérés (Japán ügyfél)

**Input:**
```
新機能の提案があります。ダッシュボードにエクスポート機能が欲しいです。 IP: 126.78.200.1
```

**Elvárt eredmény:**
- Nyelv: Japán
- Hangulat: Semleges / Pozitív
- Kategória: Feature Request
- Prioritás: P4 (Alacsony)
- Routing: Product Team

---

### 6. IP cím nélküli teszt

**Input:**
```
Nem értem a számlát, segítsenek!
```

**Elvárt eredmény:**
- Nyelv: Magyar
- Hangulat: Kissé frusztrált
- Kategória: Számlázás
- Prioritás: P3
- Megjegyzés: Nincs lokáció információ (nincs IP)

---

## LangGraph Architektúra

Az agent LangGraph StateGraph-ot használ a workflow orchestrációhoz.

### Strukturált Output (Pydantic)

A ticket elemzés Pydantic modellel és `with_structured_output()` használatával történik:

```python
class TicketAnalysis(BaseModel):
    language: str
    sentiment: Literal["frustrated", "neutral", "satisfied"]
    category: Literal["Billing", "Technical", "Account", "Feature Request", "General"]
    priority: Literal["P1", "P2", "P3", "P4"]
    routing: str

# Használat
analysis_llm = llm.with_structured_output(TicketAnalysis)
result: TicketAnalysis = analysis_llm.invoke(prompt)
```

### Workflow Diagram

```
┌─────────────────────┐
│   Ticket Input      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  analyze_ticket     │  ← LLM: nyelv, sentiment, kategória, prioritás
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │  Van IP cím? │
    └──────┬───────┘
       yes │    │ no
           ▼    │
┌─────────────────────┐    │
│   get_location      │ ←──┤ ip-api.com API
└──────────┬──────────┘    │
           │               │
           ▼               │
┌─────────────────────┐    │
│   get_holidays      │ ← Nager.Date API
└──────────┬──────────┘    │
           │               │
           ▼               │
┌─────────────────────┐◄───┘
│   calculate_sla     │  ← SLA határidő számítás
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  generate_response  │  ← LLM: magyar nyelvű válasz
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│       END           │
└─────────────────────┘
```

## Projekt Struktúra

```
mini_projects/zsolt.komlosi/ht_1/
├── main.py              # Main entry point, chat loop
├── agent.py             # LangGraph agent (StateGraph workflow)
├── models.py            # Pydantic models (TicketAnalysis)
├── tools.py             # API tools
├── config.py            # Settings (.env handling)
├── tests.py             # Unit tests (pytest)
├── Tests.md             # Test documentation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker compose config
└── README.md            # This file
```

## Technológiák

- **Python 3.11+**
- **LangGraph** - Agent workflow orchestráció (StateGraph)
- **LangChain** - LLM integráció
- **OpenAI GPT-4.1-mini** - LLM
- **Pydantic** - Adatvalidáció
- **Requests** - HTTP kliens
- **Docker** - Konténerizáció

## Házi Feladat Követelmények

| Követelmény | Teljesítve |
|-------------|------------|
| Ingyenes publikus API használata | ip-api.com, Nager.Date |
| User input bekérése | Interaktív chat |
| API hívás requests-szel | tools.py |
| Szép, emberi szöveg kimenet | Magyar nyelvű elemzés |
| LangChain/LangGraph használata | agent.py |
| OpenAI kis modell | gpt-4.1-mini |
| Konzolos felület | main.py chat loop |

