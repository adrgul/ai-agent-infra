# INIT Prompt: Regulation Agent Project Structure & Functionality

## Fájlrendszer és főbb komponensek

```
docred/
├── backend/
│   ├── domain/
│   │   ├── interfaces.py         # Absztrakt interfészek (IUserRepository, IConversationRepository, IRegulationRAGClient)
│   │   └── models.py            # Adatmodellek (UserProfile, ConversationHistory, Message, stb.)
│   ├── infrastructure/
│   │   ├── repositories.py      # Fájl alapú tárolás (felhasználók, beszélgetések)
│   │   └── tool_clients.py      # RegulationRAGClient (RAG+FAISS, csak regulation)
│   ├── services/
│   │   ├── agent.py             # LangGraph-alapú agent workflow
│   │   ├── tools.py             # RegulationTool wrapper
│   │   └── chat_service.py      # Chat workflow, session management
│   ├── main.py                  # FastAPI belépési pont
│   ├── requirements.txt         # Python függőségek
│   └── data/
│       ├── regulation_vectordb/ # FAISS indexelt szabályozási vektorok
│       ├── users/               # Felhasználói profilok (JSON)
│       └── sessions/            # Beszélgetési előzmények (JSON)
├── frontend/
│   ├── src/
│   │   ├── components/          # React komponensek (ChatWindow, MessageBubble, stb.)
│   │   ├── App.tsx, api.ts, ... # Fő alkalmazáslogika
│   ├── package.json, vite.config.ts, ...
│   └── index.html
├── docker-compose.yml           # Konténer orchestration
├── README.md                    # Részletes projektleírás, tesztesetek
└── INIT_Prompt_regulation.md    # (ez a fájl)
```

## Működési logika

- **Regulation Tool**: Retrieval-Augmented Generation (RAG) pipeline, amely a 2008. évi XL. törvény PDF-ből FAISS vektortárral keres, OpenAI embeddinggel, LangChain/Graph orchestration-nel.
- **Backend**: FastAPI REST API, LangGraph agent workflow, minden adat (user, session, regulation index) JSON vagy FAISS fájlban.
- **Frontend**: React+TypeScript, ChatGPT-szerű UI, API hívások a backendhez.
- **Persistence**: Minden üzenet, profil, session fájlban, reset context parancs törli a session-t, de a profilt nem.
- **Tesztelés**: pytest unit tesztek a RegulationTool működésére (mockolt RegulationRAGClient-tel).

## Főbb osztályok és felelősségek

- `RegulationRAGClient` (infrastructure/tool_clients.py):
  - PDF betöltés, chunkolás, embedding, FAISS indexelés/keresés
  - Kérdésre releváns szövegrészek visszaadása
- `RegulationTool` (services/tools.py):
  - Agent által hívható wrapper, hibakezelés, válasz formázás
- `Agent` (services/agent.py):
  - LangGraph workflow, döntési logika, tool hívások, végső válasz
- `ChatService` (services/chat_service.py):
  - Session, user, history kezelés, API endpointok
- `IRegulationRAGClient` (domain/interfaces.py):
  - Absztrakt interfész a regulation toolhoz

## Tesztesetek (README.md végén)
- Kérdés: "Listázd, hogy mely paragrafusok foglalkoznak az egyetemes szolgáltatóval!"
- Kérdés: "A Hivatal ... mely paragrafus és pontok szerint ... információkat kérni?"
- Várt válaszok: konkrét paragrafusok, törvényi hivatkozások, magyarázat

## Jelenlegi állapot
- Minden "book" hivatkozás törölve, csak "regulation" tool és logika van
- RegulationRAGClient az egyetlen aktív RAG-implementáció
- Minden teszt, API, workflow, dokumentáció a regulation toolra épül
- A README részletes példákat, API mintákat, teszteseteket tartalmaz

---
Ez a fájl a docred projekt jelenlegi szerkezetét és működését írja le, hogy promptként vagy dokumentációként is használható legyen.
