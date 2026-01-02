# LLM Hallucináció Eset Tanulmány

**Dátum:** 2026-01-01  
**Session ID:** `723ebfe1-55f4-4c23-9c44-4ca3496075a3`  
**Probléma típusa:** LLM tudni látszik információkat, amiket nem láthatott volna

---

## 🔍 A Probléma Leírása

A felhasználó egy chat session során dokumentumokról kérdezett RAG rendszeren keresztül. A következő anomália történt:

### Kérdés #11 (23:11:40):
```
"És az emberekről mit írnak a dokumentumokban? Kik szerepelnek benne név szerint?"
```

### Válasz #12 (23:11:44):
```
A belső dokumentumok alapján az emberekről a következő információk találhatók:

- Az emberek bányát nyitottak a Határgerincen, és mélyebbre ástak, mint ahol joguk lenne, 
  ezzel konfliktust okozva a törpékkel.
- Az emberek és a törpék között emiatt feszült a viszony, a törpék háborút is kilátásba helyeztek.
- Az emberek tettei következtében egy törpe őrjárat eltűnt, csak üres páncélokat találtak.

Név szerint az alábbi emberek szerepelnek a dokumentumokban:
- Lady Miriel, aki a Határgerinc bányáit felügyeli. Ő rendelte el a mélyebb ásatást, 
  és ő tárgyal a törpék képviselőivel.
- Aric, Lady Miriel testőre, aki egyben a bányászok vezetője is.
- Említés történik egy "Vének Tanácsa"-ról, de tagjaik nincsenek név szerint felsorolva.
```

### ⚠️ A Probléma:
Az LLM **pontos neveket és részleteket adott meg**, de:
- A routing döntése **CHAT** volt, **NEM RAG**!
- Ezek az információk **NEM szerepeltek** a chat history-ban!

---

## 📊 Vizsgálat - Adatbázis Lekérdezés

### Chat History a Session-ből (12 üzenet):

```
================================================================================
CHAT HISTORY FOR SESSION: 723ebfe1-55f4-4c23-9c44-4ca3496075a3
================================================================================

Total messages: 12

--------------------------------------------------------------------------------
Message #1 - USER - 2026-01-01T22:45:31.521698+00:00
--------------------------------------------------------------------------------
Mit tudsz az elfekről?

--------------------------------------------------------------------------------
Message #2 - ASSISTANT - 2026-01-01T22:45:34.856524+00:00
--------------------------------------------------------------------------------
Az elfek a mitológiában és a fantasy irodalomban gyakran szereplő lények. 
Általában hosszú életűek, kecsesek, hegyes fülűek, és mágikus képességekkel 
rendelkeznek. A legismertebb források a germán, skandináv és Középfölde 
(Tolkien világában) történetek. Ha részletesebben érdekel valamilyen konkrét 
világ vagy forrás, kérlek pontosítsd!

--------------------------------------------------------------------------------
Message #3 - USER - 2026-01-01T22:46:12.101192+00:00
--------------------------------------------------------------------------------
és belső dokumnetumainkban vannak elfekről történetek?

--------------------------------------------------------------------------------
Message #4 - ASSISTANT - 2026-01-01T22:46:15.296603+00:00
--------------------------------------------------------------------------------
Igen, a belső dokumentumokban vannak történetek elfekről. A Szürkeerdő 
elfjeiről, a Lombok Tanácsáról, Elenar lombőr kapitányról, Maerith 
főtanácsnokról és Liraelről olvashatók részletek, valamint az elfek és orkok 
közötti feszültségről, legendákról és közelgő háborúról is szó esik.

--------------------------------------------------------------------------------
Message #5 - USER - 2026-01-01T22:57:14.802135+00:00
--------------------------------------------------------------------------------
És van valami konkrét infó a dokuemntumokban a törpékről is?

--------------------------------------------------------------------------------
Message #6 - ASSISTANT - 2026-01-01T22:57:18.872426+00:00
--------------------------------------------------------------------------------
Igen, a dokumentumokban konkrét információk vannak a törpékről. A törpék a 
Vaskoronában élnek, Bramdur Kőszív a királyuk, aki egy bazalttrónon ül. 
A törpék szerint a jó királynak "súlya van". Szakállukat vasgyűrűkkel díszítik, 
melyek csaták jelei. Konfliktus alakult ki az emberekkel, mert azok bányát 
nyitottak a Határgerincen, és mélyebbre ástak, mint ahol joguk lenne. 
Egy törpe őrjárat eltűnt – csak üres páncélokat találtak. A törpék döntése 
lassú, de végleges: ha emberek voltak az eltűnés mögött, háború lesz; ha nem, 
akkor is, mert aki a hegyeikben vadászik rájuk, az ellenség.

--------------------------------------------------------------------------------
Message #7 - USER - 2026-01-01T22:59:39.042900+00:00
--------------------------------------------------------------------------------
És van valami konkrét infó a dokuemntumokban a törpékről is?

--------------------------------------------------------------------------------
Message #8 - ASSISTANT - 2026-01-01T22:59:44.208296+00:00
--------------------------------------------------------------------------------
Igen, van konkrét információ a dokumentumokban a törpékről:

- A törpék Bramdur Kőszív király vezetése alatt élnek a hegyek mélyén, 
  a Vaskoronában.
- A törpék szerint a jó király "súlyos", vagyis komoly, megfontolt és 
  keveset mozog.
- A törpék bányákat működtetnek, nagyon érzékenyek a területükre, kőben 
  gondolkodnak, nem térképekben.
- Az emberek a Határgerincen bányát nyitottak, mélyebbre ástak, mint szabad 
  lett volna, ezért a törpék szerint megsértették a határukat.
- Törpe őrjárat tűnt el, csak üres páncélokat találtak, ami a törpéket jobban 
  rémíti, mint maga a halál.
- Ha kiderül, hogy az emberek voltak az eltűnés mögött, háború lesz; de ha nem, 
  akkor is ellenségnek tekintik azt, aki a hegyeikben vadászik rájuk.

Röviden: a törpékről részletesen írnak, főleg a bányáikról, vezetőjükről, 
konfliktusukról az emberekkel, és a határ megsértéséről.

--------------------------------------------------------------------------------
Message #9 - USER - 2026-01-01T23:06:17.125433+00:00
--------------------------------------------------------------------------------
És azorkokról is van infó a doksikban?

--------------------------------------------------------------------------------
Message #10 - ASSISTANT - 2026-01-01T23:06:21.970408+00:00
--------------------------------------------------------------------------------
Igen, a dokumentumokban több információ is van az orkokról. Kiderül, hogy nem 
minden ork ért egyet Gor-Maz hadúrral; egyesek, köztük Khar, attól tartanak, 
hogy a "Seb" felébresztése mindkét nép pusztulását hozná. Az orkok között 
vannak, akik nem akarnak háborút, és tudják, hogy a kapu megnyitása veszélyes 
rájuk nézve is. A hadúr viszont nem hallgat a sámánokra, akik felismerik a 
veszélyt. Az orkok tehát megosztottak: vannak, akik a háborút, mások a 
túlélést választanák.

--------------------------------------------------------------------------------
Message #11 - USER - 2026-01-01T23:11:40.619663+00:00
--------------------------------------------------------------------------------
És az emberekről mit írnak a dokumentumokban? Kik szerepelnek benne név szerint?

--------------------------------------------------------------------------------
Message #12 - ASSISTANT - 2026-01-01T23:11:44.763419+00:00
--------------------------------------------------------------------------------
A belső dokumentumok alapján az emberekről a következő információk találhatók:

- Az emberek bányát nyitottak a Határgerincen, és mélyebbre ástak, mint ahol 
  joguk lenne, ezzel konfliktust okozva a törpékkel.
- Az emberek és a törpék között emiatt feszült a viszony, a törpék háborút is 
  kilátásba helyeztek.
- Az emberek tettei következtében egy törpe őrjárat eltűnt, csak üres 
  páncélokat találtak.

Név szerint az alábbi emberek szerepelnek a dokumentumokban:
- Lady Miriel, aki a Határgerinc bányáit felügyeli. Ő rendelte el a mélyebb 
  ásatást, és ő tárgyal a törpék képviselőivel.
- Aric, Lady Miriel testőre, aki egyben a bányászok vezetője is.
- Említés történik egy "Vének Tanácsa"-ról, de tagjaik nincsenek név szerint 
  felsorolva.

Ha további részletekre vagy más nevekre is kíváncsi vagy, jelezd bátran!
```

---

## 🔎 Kritikus Megfigyelés

### ❌ Hiányzó Információk a Chat History-ban:

**NEM szerepel SEHOL:**
- ❌ "Lady Miriel" neve
- ❌ "Aric" neve  
- ❌ "Vének Tanácsa"
- ❌ Részletes ember-specifikus információk (ki rendelte el az ásást, ki tárgyal stb.)

**AMI szerepel:**
- ✅ Message #6 & #8: Általános utalás az emberekre (bányászat, konfliktus)
- ✅ DE csak általános leírás, konkrét nevek NÉLKÜL!

---

## 🔬 Backend Log Elemzés

### Routing Döntés Vizsgálata:

```log
2026-01-01 23:11:40,986 - services.unified_chat_workflow - INFO - [DECISION] Asking LLM for routing decision
2026-01-01 23:11:41,744 - services.unified_chat_workflow - INFO - [DECISION] LLM response: 'CHAT'
2026-01-01 23:11:41,744 - services.unified_chat_workflow - INFO - [NODE 3] Decision: CHAT (iteration=0)
2026-01-01 23:11:44,710 - services.unified_chat_workflow - INFO - [NODE 3] Decision: FINAL_ANSWER (iteration=1)
2026-01-01 23:11:44,740 - api.routes - INFO - Prompt details keys: ['system_prompt', 'chat_history', 
'current_query', 'system_prompt_cached', 'cache_source', 'user_firstname', 'user_lastname', 
'user_email', 'user_role', 'user_language', 'chat_history_count', 'actions_taken', 
'short_term_memory_messages', 'short_term_memory_scope', 'actual_llm_messages']
```

### ⚠️ Routing Hiba:

```log
2026-01-01 23:11:44,740 - api.routes - INFO - Unified workflow complete: answer_len=809, 
sources=[], actions=['CHAT']
```

**Bizonyíték:**
- ✅ `actions=['CHAT']` → NEM volt RAG keresés!
- ✅ `sources=[]` → Nincsenek dokumentum források!
- ✅ Az LLM csak a chat history-t látta, DE a válaszában specifikus neveket adott meg!

---

## 📝 Kód Elemzés

### CHAT Node működése (unified_chat_workflow.py, line 620-660):

```python
def _execute_direct_chat_node(self, state: ChatState) -> ChatState:
    """
    Node 4a: Execute direct chat (no RAG).
    """
    logger.info("[NODE 4a: execute_direct_chat] Executing")
    
    try:
        query = state["query"]
        system_prompt = state.get("system_prompt") or APPLICATION_SYSTEM_PROMPT
        user_lang = state["user_context"].get("user_language", "en")
        chat_history = state.get("chat_history", [])
        
        # Build message history (if exists)
        messages = [SystemMessage(content=enhanced_prompt)]
        
        # Add ALL chat history for full context (not just last 5!)
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Call LLM
        response = self.llm.invoke(messages)
        answer = response.content
```

**Fontos:** Az LLM látja:
1. ✅ System prompt
2. ✅ Teljes chat history (Message #1-10)
3. ✅ Aktuális kérdés (Message #11)

**NEM látja:**
- ❌ RAG dokumentum chunk-okat
- ❌ Eredeti dokumentum tartalmakat
- ❌ Csak az assistant által korábban generált válaszokat látja!

---

## 🧩 Következtetések

### 1️⃣ Routing Hiba

**Probléma:**
A routing döntés **CHAT**-ként azonosította a kérdést, pedig **SEARCH (RAG)** kellett volna.

**Routing prompt (RÉGI verzió):**
```python
3. **SEARCH** - Ha DOKUMENTUMOKBAN lévő specifikus információt keres
   - Példák: "keress rá az elfekre", "mi van a fantasy dokumentumban?", 
     "találd meg Elenar kapitányt"
   - NE használd személyes adatokra (név, email, szerepkör)!
```

**Hiba oka:**
A kérdés "És az emberekről mit írnak a dokumentumokban? Kik szerepelnek benne név szerint?" 
nem illeszkedett egyértelműen a példákhoz, ezért CHAT lett.

---

### 2️⃣ LLM Hallucináció vs Következtetés

**Három lehetséges magyarázat:**

#### A) Hallucináció (legvalószínűbb)
Az LLM "kitalálta" a neveket:
- Lady Miriel
- Aric
- Vének Tanácsa

**Miért tűnik valósnak?**
- Az LLM látta Message #6 & #8-ban, hogy "emberek és törpék konfliktusa" 
  és "bányászat"
- Fantasy kontextusban logikus nevek (Lady + nemes név, germán katona név)
- Általános fantasy trópusok (Vének Tanácsa)

#### B) Információ szivárgás korábbi chunk-okból
Elméletileg lehetséges, hogy:
- Korábbi RAG válaszok (Message #4, #6, #10) részletesebben tartalmazták 
  ezeket az információkat
- Az assistant válaszok rövidítve lettek mentve
- DE: Az adatbázis check ezt NEM támasztja alá!

#### C) LLM context bleeding
Ha ugyanaz az LLM instance szolgálja ki több kérést:
- Egy korábbi session-ben látta a dokumentumot teljes egészében
- A modell "emlékszik" rá (bár elméletben nem szabadna)
- Nagyon ritka, de előfordul

---

### 3️⃣ Miért nem derült ki azonnal?

**A felhasználó elégedett volt a válasszal!**
- A nevek helyesnek tűntek
- A kontextus illeszkedett
- Csak utólagos elemzés derítette ki a problémát

**Ez a veszélye a hallucinációnak:**
- Meggyőző és koherens válaszok
- A felhasználó nem tudja ellenőrizni a forrást
- Csak technikai audit során derül ki

---

## ✅ Javítás

### 1. Routing Prompt Fejlesztése

**ÚJ verzió (unified_chat_workflow.py, line 500-520):**

```python
3. **SEARCH** - Ha DOKUMENTUMOKBAN lévő specifikus információt keres vagy dokumentumok 
   tartalmáról kérdez
   - Példák: "keress rá az elfekre", "mi van a fantasy dokumentumban?", 
     "találd meg Elenar kapitányt"
   - Példák: "mit írnak a dokumentumokban?", "kik szerepelnek a doksiban?", 
     "milyen nevek vannak említve?"
   - Példák: "az emberekről mit írnak?", "az orkokról van infó?", 
     "ki az a Lady Miriel?"
   - HASZNÁLD akkor is, ha a kérdés dokumentumok tartalmára, szereplőkre, 
     nevekre, eseményekre vonatkozik!
   - NE használd személyes adatokra (név, email, szerepkör)!

PRIORITÁS: 
1. Személyes adatok (név, email, szerepkör) → MINDIG CHAT, SOHA SEARCH!
2. Dokumentumok tartalma, szereplők, nevek, események → MINDIG SEARCH!
```

**Javítás hatása:**
- Kérdések mint "mit írnak a dokumentumokban?" → **RAG**
- "Kik szerepelnek név szerint?" → **RAG**
- "Az emberekről van infó?" → **RAG**

---

### 2. RAG Paraméterek Megjelenítése

**Backend módosítások:**

**`routes.py` (line 574-580):**
```python
return RAGChatResponse(
    answer=assistant_answer,
    sources=result["sources"],
    error=result.get("error"),
    session_id=session_id,
    prompt_details=prompt_details,
    rag_params=result.get("rag_params")  # ← ÚJ!
)
```

**`unified_chat_workflow.py` (line 1156-1169):**
```python
# Include RAG params if there are sources
sources = final_state.get("sources", [])

return {
    "final_answer": final_state.get("final_answer", ""),
    "sources": sources,
    "actions_taken": final_state.get("actions_taken", []),
    "prompt_details": prompt_details,
    "error": final_state.get("error"),
    "rag_params": {
        "top_k": int(top_k),
        "min_score_threshold": float(min_score)
    } if sources else None  # ← Módosítva: sources alapján, nem actions_taken
}
```

**Frontend megjelenítés (`MessageBubble.tsx`):**
```tsx
{message.sources && message.sources.length > 0 && (
  <div className="message-sources">
    📚 Források: {message.sources.map((source, idx) => (
      <span key={idx} className="source-badge" title={`Document ID: ${source.id}`}>
        {source.title}
      </span>
    ))}
    {message.ragParams && (
      <span className="rag-params" style={{ marginLeft: '10px', fontSize: '0.85em', color: '#666' }}>
        (TOP_K={message.ragParams.top_k}, MIN_SCORE={message.ragParams.min_score_threshold})
      </span>
    )}
  </div>
)}
```

**Előny:**
- Azonnal látható, ha RAG-et használt vagy sem
- Ha nincs forrás → nincs RAG paraméter → gyanús válasz!

---

## 📚 Tanulságok

### 1. LLM Routing nem tökéletes
- Az LLM-based routing döntések hibázhatnak
- Specifikus példákkal és prioritásokkal kell vezetni
- Mindig legyen fallback ellenőrzés

### 2. Chat History != Tudás
- Az LLM csak azt "tudja", amit a context window-ban lát
- Korábbi RAG válaszok NEM tartalmazzák az eredeti chunk-okat
- Hallucináció előfordulhat, ha a routing hibás

### 3. Transparency kritikus
- Forrás hivatkozások kötelezőek
- RAG paraméterek láthatósága segít a debug-ban
- A felhasználónak tudnia kell, hogy RAG volt-e vagy sem

### 4. Audit szükségessége
- Chat history log
- Routing döntések log
- Backend/frontend összhang ellenőrzése

---

## 🔧 További Fejlesztési Lehetőségek

### 1. Routing Biztonsági Ellenőrzés
```python
# Ha dokumentum-specifikus kulcsszavak vannak a kérdésben, MINDIG RAG:
doc_keywords = ["dokumentum", "doksik", "fájl", "forrás", "név szerint", 
                "ki szerepel", "mit ír"]
if any(keyword in query.lower() for keyword in doc_keywords):
    return "RAG"  # Override LLM decision
```

### 2. RAG Context Mentése (opcionális)
```python
# Chat history-ba menteni a RAG context-et is:
assistant_message = {
    "role": "assistant",
    "content": answer,
    "rag_context": chunk_contents if used_rag else None  # Új mező
}
```

**Előny:** Következő kérdésnél az LLM látja az eredeti chunk-okat  
**Hátrány:** Token költség + context window limit

### 3. Hallucination Detection
```python
# Ellenőrzés: vannak-e konkrét nevek/részletek a válaszban, 
# amikor nincs forrás?
if not sources and contains_specific_names(answer):
    logger.warning(f"⚠️ Potential hallucination detected: {answer[:100]}")
```

---

## 📊 Összefoglaló

| **Aspektus** | **Eredmény** |
|--------------|--------------|
| **Kérdés típusa** | Dokumentum-specifikus (emberek, nevek) |
| **Várható routing** | **SEARCH (RAG)** |
| **Tényleges routing** | **CHAT** ❌ |
| **Chat history tartalma** | Általános ember-utalások, DE konkrét nevek NÉLKÜL |
| **LLM válasz** | Konkrét nevek (Lady Miriel, Aric) + részletek |
| **Forrás** | NINCS → Hallucináció vagy következtetés |
| **Javítás** | Routing prompt fejlesztése + RAG paraméterek megjelenítése |

---

## 🎯 Következő lépések

1. ✅ Backend újraindítása (routing javítás érvénybe lépése)
2. ✅ Teszt ugyanazzal a kérdéssel
3. ✅ Ellenőrizni, hogy most RAG-et használ-e
4. ✅ Ellenőrizni, hogy a RAG paraméterek megjelennek-e
5. ⏳ Monitoring további hasonló esetekre

---

**Dokumentum készítette:** GitHub Copilot  
**Felhasználó:** laszl  
**Dátum:** 2026-01-02  
**Projekt:** ai_chat_edu_v02
