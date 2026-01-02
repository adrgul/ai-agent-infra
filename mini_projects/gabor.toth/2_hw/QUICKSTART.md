# 🚀 QUICKSTART - Teljes Demo Workflow

Ez az útmutató részletesen leírja, hogyan futtasd az alkalmazást és végezz el egy teljes demó workflow-t:
1. Szerver indítása
2. HR és AI kategóriák létrehozása
3. Demo dokumentumok feltöltése
4. Tesztkérdések feldolgozása
5. Irreleváns kérdések kezelésének megfigyelése

---

## 1️⃣ Szerver Indítása

### 1.1 Környezeti Változók Beállítása

```bash
# Navigálj a 2_hw mappához
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw

# Ellenőrizd, hogy a .env fájl létezik-e
ls -la .env

# Ha nem létezik, másolj az .env.example-ből
cp .env.example .env

# Szerkeszd a .env-et és add meg az OpenAI API kulcsod
# nano .env
# vagy
# open .env  (macOS)
```

**Szükséges env vars:**
```
OPENAI_API_KEY=sk-... (szupertitkos)
PYTHONUNBUFFERED=1
```

### 1.2 Szerver Indítása

```bash
# Az indítás a source .env && ./start-dev.sh paranccsal

source .env && ./start-dev.sh
```

**Amit látni fogsz:**
```
🔓 Portok felszabadítása (8000, 5173)...
📁 Adatmappák létrehozása...
🖥️ Backend indítása (FastAPI)...
  ✓ http://localhost:8000/api/health ← Fut-e?
🎨 Frontend indítása (React + Vite)...
  ✓ http://localhost:5173 ← Nyisd meg böngészőben

Az Activity Logger panel már látható a jobb felső sarokban!
```

### 1.3 Szerver Ellenőrzése

Másik terminálban teszteld, hogy az API működik:

```bash
# Health check
curl http://localhost:8000/api/health
# Válasz: {"status": "ok"}
```

---

## 2️⃣ Kategóriák Létrehozása

### 2.1 HR Kategória

A **Frontend** UI-on (http://localhost:5173):

1. **Kattints a "Dokumentum Feltöltés" panelra**
   - Jobb oldalon találod a feltöltési interfészt
   
2. **Kattints a "➕ Új Kategória" gombra**
   - Megjelenít egy input mezőt

3. **Írj be: `HR`**
   ```
   Kategória neve: HR
   ```

4. **Kattints az "✓ Mentés" gombra**

5. **Az Activity Logger ezt mutatja:**
   ```
   🏷️ Kategória létrehozva: HR
   ```

### 2.2 AI Kategória

Ugyanezt ismételd meg az AI kategóriával:

1. **Kattints a "➕ Új Kategória" gombra**
2. **Írj be: `AI`**
3. **Kattints az "✓ Mentés" gombra**
4. **Az Activity Logger ezt mutatja:**
   ```
   🏷️ Kategória létrehozva: AI
   ```

### 2.3 Ellenőrzés

Az App.tsx a user profilt erre módosította:
```json
{
  "username": "gabor.toth",
  "categories": {
    "HR": { "description": "HR kategória dokumentumai", ... },
    "AI": { "description": "AI kategória dokumentumai", ... }
  }
}
```

---

## 3️⃣ Demo Dokumentumok Feltöltése

### 3.1 HR Dokumentum Feltöltése

#### **Fájl:** `DEMO_files_for_testing/HR_demo_hu.md`

**Tartalom:** Munka Törvénykönyve – 11 szakasz:
- A törvény célja és hatálya
- Munkaszerződés alapjai
- Munkaidő és munkarend
- Munkabér és bérfizetés
- Szabadság és távollétek
- Felmondás és megszüntetés
- stb.

**Feltöltés lépései:**

1. **Frontend UI - HR Kategória Kiválasztása**
   - A "Kategória Kiválasztása" dropdown-ot nyisd le
   - Válaszd ki: **HR**

2. **Kattints "Fájl Kiválasztása" gombra**
   - Navigálj ide: `/Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw/DEMO_files_for_testing/`
   - Válaszd ki: **HR_demo_hu.md**

3. **Kattints az "Feltöltés" gombra**

4. **Activity Logger nyomon követése** (Valós idejű események):
   ```
   📄 Dokumentum feldolgozása: HR_demo_hu.md (kategória: HR)
   📖 Szöveg kinyerése: 7250 karakter feldolgozva
   ✂️ Chunkolás: 18 chunk-ra felosztva (átl. 403 karakter/chunk)
   🔗 Embedding generálása: 18 vektor feldolgozása (OpenAI API)
   📊 Vektor-indexelés: ChromaDB-ben tárolva
   💾 Metadata mentése: chunks.json frissítve
   ✅ Feltöltés sikeresen befejezve! (3.2s alatt)
   ```

### 3.2 AI Dokumentum Feltöltése

#### **Fájl:** `DEMO_files_for_testing/AI_vector_demo_hu.md`

**Tartalom:** RAG + Vektoradatbázis – 3 nagy szakasz:
- Miért kell RAG egy agentnek?
- RAG referencia-architektúra röviden
- Vektoradatbázis és embedding

**Feltöltés lépései:**

1. **Frontend UI - AI Kategória Kiválasztása**
   - A "Kategória Kiválasztása" dropdown-ot nyisd le
   - Válaszd ki: **AI**

2. **Kattints "Fájl Kiválasztása" gombra**
   - Navigálj ide: `/Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw/DEMO_files_for_testing/`
   - Válaszd ki: **AI_vector_demo_hu.md**

3. **Kattints az "Feltöltés" gombra**

4. **Activity Logger nyomon követése**:
   ```
   📄 Dokumentum feldolgozása: AI_vector_demo_hu.md (kategória: AI)
   📖 Szöveg kinyerése: 14532 karakter feldolgozva
   ✂️ Chunkolás: 35 chunk-ra felosztva (átl. 415 karakter/chunk)
   🔗 Embedding generálása: 35 vektor feldolgozása (OpenAI API)
   📊 Vektor-indexelés: ChromaDB-ben tárolva
   💾 Metadata mentése: chunks.json frissítve
   ✅ Feltöltés sikeresen befejezve! (5.8s alatt)
   ```

### 3.3 Mi Történik a Háttérben?

**Feltöltés után a `data/` mappa:**
```
data/
├── users/
│   └── gabor.toth.json              # Kategóriák mentve: HR, AI
│
├── uploads/
│   └── gabor.toth/
│       ├── HR_demo_hu.md            # Feltöltött fájl
│       └── AI_vector_demo_hu.md     # Feltöltött fájl
│
├── derived/
│   └── chunks.json                  # 18 + 35 = 53 chunk összesen
│
└── chroma_db/                       # Vektorok ChromaDB-ben
    ├── HR_collection/               # 18 vektor (HR kategória)
    └── AI_collection/               # 35 vektor (AI kategória)
```

**Chunks.json szerkezete:**
```json
{
  "HR": {
    "HR_demo_hu.md": {
      "chunks": [
        {
          "id": "HR_demo_hu_chunk_1",
          "text": "A szabályozás a tisztességes foglalkoztatás alapvető kereteit...",
          "embedding": [0.123, -0.456, ...],
          "start_char": 0,
          "end_char": 403,
          "metadata": {
            "source": "HR_demo_hu.md",
            "uploaded_by": "gabor.toth",
            "uploaded_at": "2026-01-01T14:30:00"
          }
        },
        { ... 17 további chunk ... }
      ]
    }
  },
  "AI": {
    "AI_vector_demo_hu.md": {
      "chunks": [
        { ... 35 chunk ... }
      ]
    }
  }
}
```

---

## 4️⃣ Tesztkérdések - Szisztematikus Tesztelés

### 4.1 HR Kérdések (10 db)

**Fájl:** `TESZT_QUESTIONS_FOR_THE_DEMO_FILES/HR_demo_tesztkérdések.md`

Minden kérdést gépelj be a **Chat** panelbe, és figyeld az alábbakat:

#### Kérdés 1: `Mi a különbség a munkaidő és a munkaidő-beosztás között, és miért fontos ez vitás helyzetben?`

**Várható viselkedés:**
```
🎯 Kategória felismerve: HR
🔍 Dokumentum keresése (HR kategória)
📚 3-4 chunk találva, átl. 0.85 hasonlóság
🤖 Válasz generálása OpenAI API-val
✅ Válasz kész!
```

**Válasz tartalmaz:**
- ✅ Definíciókat (munkaidő vs. munkaidő-beosztás)
- ✅ Jogi relevanciát (vitás helyzetben)
- ✅ Kattintható chunk hivatkozásokat: `[[HR_demo_hu_chunk_X | 0.87]]`

#### Kérdés 2: `Milyen helyzetekben lehet releváns a munkaidőkeret, és milyen nyilvántartások szükségesek hozzá?`

**Várható viselkedés:**
```
🎯 Kategória felismerve: HR
🔍 Dokumentum keresése (HR kategória)
📚 2-3 chunk találva, átl. 0.82 hasonlóság
🤖 Válasz generálása OpenAI API-val
✅ Válasz kész!
```

**Válasz tartalmaz:**
- ✅ Munkaidőkeret definíciója
- ✅ Nyilvántartási követelmények
- ✅ Chunk hivatkozások: `[[HR_demo_hu_chunk_4 | 0.84]]`

#### Kérdések 3-10

Ugyanez az eljárás az alábbi kérdésekre:

```
3. Mikor minősül a munkavégzés rendkívüli munkának, és milyen tipikus következményei vannak?
4. Hogyan viszonyul egymáshoz a napi pihenőidő, a heti pihenő és a munkaközi szünet logikája?
5. Milyen fő elemeket szokás munkaszerződésben rögzíteni, és mi kerül gyakran külön tájékoztatóba?
6. Milyen elvi korlátai vannak a munkáltatói utasítási jognak, és mikor merülhet fel az utasítás megtagadása?
7. Miben különbözik a közös megegyezés, a felmondás és az azonnali hatályú megszüntetés gyakorlati logikája?
8. Milyen feltételekhez kötött a munkabérből történő levonás a kár megtérítése érdekében?
9. Miért nem "egymondatos" kérdés a a munkavállalói kárfelelősség, és milyen tényezőket kell tisztázni a döntéshez?
10. Milyen szerepet töltenek be a belső szabályzatok és kollektív megállapodások a törvényi keretek mellett?
```

### 4.2 AI Kérdések (10 db)

**Fájl:** `TESZT_QUESTIONS_FOR_THE_DEMO_FILES/AI_vector_demo_tesztkérdések.md`

Ugyanez az eljárás, de az AI kategóriás kérdésekre:

```
1. Mi a különbség a hibrid keresés és a tisztán vektoros keresés között, és mikor melyiket érdemes választani?
2. Miért szükséges a LLM szövegkereső agent esetén az overlap a chunkok között, és mekkora legyen tipikusan százalékosan?
3. Milyen metadata mezők a leghasznosabbak a RAG adatbázidokban, LLM segítségével történő szűrt visszakereséshez és auditáláshoz?
4. Hogyan mérnéd a RAG adatbázisból, LLM felhasználásával elvégzett retrieval minőséget, ha nincs címkézett tanító/adatod?
5. Miért javasolt kétlépcsős retrieval (recall-orientált első kör + re-ranking)?
6. Mik a leggyakoribb hibaminták, ha a modell "talál, mégis rosszul válaszol"?
7. Hogyan kezelnéd a LLM-el támogatott tudásbázisokonban a dokumentumok verziózását és a régi chunkok "kiszorítását" az indexből?
8. Mit jelent a groundedness, és hogyan kényszerítenéd ki, hogy az LLM által adott válasz csak forrásokból dolgozzon?
9. Mikor érdemes query rewritinget és multi-queryt használni, és hogyan hat ez a recallra?
10. Hogyan kezelnéd a táblázatos adatokat chunkoláskor, hogy a sorok önmagukban is érthetők legyenek az LLM-el történő feldolgozáshoz?
```

### 4.3 Mi Történik Minden Kérdésnél?

**Activity Logger Nyomon Követése:**

```
1️⃣ KATEGÓRIA-ROUTING (LLM döntés)
   💬 Kérdés feldolgozása
   🎯 Kategória felismerése (HR vagy AI?)
   → Keresés az adott kategóriában

2️⃣ VEKTOR-KERESÉS (Embedding hasonlóság)
   🔍 Dokumentum keresése
   📚 N chunk találva, átl. X.XX hasonlóság
   → Top-5 chunk a ChromaDB-ből

3️⃣ RAG VÁLASZ-GENERÁLÁS
   🤖 Válasz generálása OpenAI API-val
   → LLM feldolgozza a kontextusokat
   → Chunk hivatkozások hozzáadódnak

4️⃣ BEFEJEZÉS
   ✅ Válasz kész! (X.Xs alatt)
   → A válasz megjelenik chunk linkekkel
```

### 4.4 Chunk Modal Megnyitása

Az LLM válaszban kattints egy chunk hivatkozásra:
```
[[HR_demo_hu_chunk_3 | 0.88 hasonlóság]]
```

**Modal panel megnyitódik:**
```
╔════════════════════════════════════════╗
║  Chunk: HR_demo_hu_chunk_3             ║
║  Hasonlóság: 0.88 (88%)                ║
║  ────────────────────────────────────  ║
║  "A munkaidőkeret olyan eszköz, amely  ║
║   lehetővé teszi, hogy a munkaidő      ║
║   elszámolása ne naponta, hanem        ║
║   hosszabb időszak átlagában történjen" ║
║  ────────────────────────────────────  ║
║  Forrás: HR_demo_hu.md                 ║
║  Feltöltés: 2026-01-01 14:30:00        ║
║  ────────────────────────────────────  ║
║  További relevás chunkok:             ║
║  • Chunk 2 (0.84)                      ║
║  • Chunk 5 (0.79)                      ║
║  • Chunk 7 (0.76)                      ║
╚════════════════════════════════════════╝
```

---

## 5️⃣ Irreleváns Kérdések Kezelése

Ez a teszt arra célja, hogy lásd: **mit csinál az alkalmazás, ha olyan kérdés érkezik, ami nem kapcsolódik az alap dokumentumokhoz**.

### 5.1 Irreleváns HR Kérdés

**Gépelj be:** `"Mekkora a Mars sugara?"`

**Várható viselkedés:**

```
🎯 Kategória felismerése...
  LLM: "Ez nem HR/AI kérdés, de próbálom az HR-ban"
  → HR kategóriában keres

🔍 Dokumentum keresése (HR kategória)
  ⚠️ Fallback keresés aktiválva
  → Nem találtam releváns chunkok (< 0.6 hasonlóság)

🔍 Dokumentum keresése (összes kategória)
  📚 0-1 chunk találva, átl. 0.45 hasonlóság
  ⚠️ Alacsony hasonlóság (< 0.6)

🤖 Válasz generálása OpenAI API-val
  (az LLM ismeri a szabad tudásbázisából, de nem idézi forrásokat)

✅ Válasz kész!
```

**Válasz tartalma:**
```
"Sajnos a feltöltött dokumentumok nem tartalmaznak információt 
a Mars sugaráról. Az alkalmazás csak a HR és AI kategóriákban 
tárolt dokumentumokra épít. 

Általános tudásból: A Mars sugara körülbelül 3,390 km, 
de ezt nem a feltöltött dokumentumok alapján válaszolom."

⚠️ MEGJEGYZÉS: Nincsenek chunk hivatkozások, mert az LLM 
nem tudott a dokumentumokból válaszolni.
```

### 5.2 Irreleváns AI Kérdés

**Gépelj be:** `"Mi az a sushi?"`

**Várható viselkedés:**

```
🎯 Kategória felismerése...
  LLM: "Ez nem AI-kérdés, próbálok keresni"
  
🔍 Dokumentum keresése (AI kategória, majd fallback)
  📚 0-1 chunk találva, átl. 0.32 hasonlóság
  ⚠️ Nagyon alacsony hasonlóság

🤖 Válasz generálása OpenAI API-val
  (szabad tudásból válaszol, nem AI dokumentumokból)

✅ Válasz kész!
```

**Válasz tartalma:**
```
"A sushi egy tradicionális japán étel. Sajnos az alkalmazás 
nem rendelkezik sushi-ről szóló dokumentumokkal. 

A feltöltött dokumentumaink az AI és HR témakörökre fókuszálnak."

⚠️ MEGJEGYZÉS: Nincsenek chunk hivatkozások.
```

### 5.3 Félig Releváns Kérdés

**Gépelj be:** `"Mi az a neural network?"`

**Várható viselkedés:**

```
🎯 Kategória felismerése...
  LLM: "Ez az AI témához köthető"
  → AI kategóriában keres

🔍 Dokumentum keresése (AI kategória)
  📚 2-3 chunk találva, átl. 0.68 hasonlóság
  ✓ Találtam relevans chunkok az "embedding" és "vektoradatbázis" témáról

🤖 Válasz generálása OpenAI API-val
  (a dokumentumok az agent-ekről, RAG-ról, embeddinghről szólnak)

✅ Válasz kész!
```

**Válasz tartalma:**
```
"A neural network-ök (neurális hálózatok) az AI alapvető 
building blockjai. Az alkalmazás dokumentumaiban az embedding-ek 
és a vektoradatbázisok kapcsán kerülnek említésre:

[[AI_vector_demo_chunk_8 | 0.71 hasonlóság]]

'Az embedding vektor egy numerikus reprezentáció, amely az 
adott szöveg szemantikáját fejezi ki. A neural network-ök 
segítségével hozza létre az OpenAI API az embedding vektorokat.'

Azonban direkt neural network architektúra-kérdésekre nincs 
részletes dokumentáció az alkalmazásban."

⚠️ MEGJEGYZÉS: Van chunk hivatkozás, de magas hasonlóság nincs 
(0.71 csak félig releváns).
```

---

## 6️⃣ Tesztelési Checklist

Használd ezt a checklistet a demo workflow-hoz:

```
SZERVER INDÍTÁSA
☐ .env fájl létezik és tartalmazza az OPENAI_API_KEY-t
☐ source .env && ./start-dev.sh sikeresen elindult
☐ http://localhost:5173 megnyitható böngészőben
☐ http://localhost:8000/api/health 200 OK

KATEGÓRIÁK LÉTREHOZÁSA
☐ HR kategória sikeresen létrehozva
☐ AI kategória sikeresen létrehozva
☐ Activity Logger mutatja: "🏷️ Kategória létrehozva: HR"
☐ Activity Logger mutatja: "🏷️ Kategória létrehozva: AI"

DOKUMENTUMOK FELTÖLTÉSE
☐ HR_demo_hu.md sikeresen feltöltve HR kategóriához
☐ AI_vector_demo_hu.md sikeresen feltöltve AI kategóriához
☐ Activity Logger mutatja mindkét feltöltésnél: "✅ Feltöltés sikeresen befejezve!"
☐ data/derived/chunks.json tartalmazza a chunkokat (18 + 35)

HR KÉRDÉSEK (10)
☐ Kérdés 1: "Mi a különbség a munkaidő és a munkaidő-beosztás között..."
   ✓ Válasz HR kategóriából származik
   ✓ Van chunk hivatkozás
   ✓ Hasonlóság > 0.80

☐ Kérdés 2: "Milyen helyzetekben lehet releváns a munkaidőkeret..."
   ✓ Válasz HR kategóriából
   ✓ Van chunk hivatkozás
   ✓ Hasonlóság > 0.78

☐ Kérdés 3-10: Hasonló viselkedés
   ✓ Mindig HR kategóriában keres
   ✓ Mindig van chunk hivatkozás
   ✓ Activity Logger: sikeres pipeline

AI KÉRDÉSEK (10)
☐ Kérdés 1: "Mi a különbség a hibrid keresés és a tisztán vektoros keresés között..."
   ✓ Válasz AI kategóriából származik
   ✓ Van chunk hivatkozás
   ✓ Hasonlóság > 0.80

☐ Kérdés 2-10: Hasonló viselkedés
   ✓ Mindig AI kategóriában keres
   ✓ Mindig van chunk hivatkozás
   ✓ Activity Logger: sikeres pipeline

IRRELEVÁNS KÉRDÉSEK
☐ "Mekkora a Mars sugara?"
   ✓ Nincsenek chunk hivatkozások (< 0.6 hasonlóság)
   ✓ LLM szabad tudásból válaszol
   ✓ Activity Logger: ⚠️ Fallback keresés aktiválva

☐ "Mi az a sushi?"
   ✓ Nincsenek chunk hivatkozások
   ✓ Alacsonysimilitás a dokumentumokhoz

☐ "Mi az a neural network?"
   ✓ Van chunk hivatkozás (0.65-0.75 hasonlóság)
   ✓ AI kategóriában talált valamit
   ✓ Válasz félig releváns

ACTIVITY LOGGER
☐ Panel megnyitható/zárható (📋 Tevékenység gomb)
☐ Kiterjeszthető teljes képernyőre (🔼/🔽)
☐ Törölhető az összes log (🗑)
☐ Szín-kódozás helyes (kék/narancssárga/zöld/piros)
☐ Timestamp helyesen jelenik meg (HH:MM:SS)
☐ Eventek időrendben vannak (legfrissebb felül)

ADATPERZISZTENCIA
☐ data/users/gabor.toth.json tartalmazza a HR és AI kategóriákat
☐ data/sessions/ tartalmaz session JSON-t
☐ data/uploads/gabor.toth/ tartalmazza a dokumentumokat
☐ data/derived/chunks.json tartalmazza a feldolgozott chunkokat
```

---

## 7️⃣ Hibaelhárítás

### A szerver nem indul el

```bash
# 1. Ellenőrizd az OpenAI API kulcsot
echo $OPENAI_API_KEY
# Kell, hogy kiírja az sk-... értéket

# 2. Újra töltsd be a .env fájlt
source .env

# 3. Próbáld újra
./start-dev.sh
```

### Az Activity Logger nem frissül

```bash
# 1. Nyisd meg a böngésző developer konzolját (F12)
# 2. Nézd meg a Network fájlt
# 3. Kattints egy kérdésre és nézd meg a fetch hívásokat

# 4. Terminal-ben teszteld az API-t
curl http://localhost:8000/api/activities
# Kell, hogy választ adjon egy JSON listával
```

### A dokumentum feltöltés sikertelen

```bash
# 1. Ellenőrizd a fájlnév helyességét
ls -la "DEMO_files_ for_testing/"

# 2. Nézd meg a backend logot
# (Az Activity Logger-ben: ❌ Fájl feldolgozási hiba)

# 3. Terminal-ben nézd meg:
tail -f backend/main.log
```

### Az LLM válasz nem érkezik meg

```bash
# 1. Ellenőrizd az OpenAI API kvótádat
# https://platform.openai.com/account/billing/limits

# 2. Nézd meg a backend logot
# 3. Activity Logger: 🤖 Válasz generálása...
#    (ha nem jelenik meg: sikertelen LLM hívás)
```

---

## 📋 Összefoglalás

```
WORKFLOW:
1. Szerver indítása (./start-dev.sh)
2. HR és AI kategóriák létrehozása
3. HR_demo_hu.md feltöltése HR-hez
4. AI_vector_demo_hu.md feltöltése AI-hez
5. 10 HR tesztkérdés feldolgozása
6. 10 AI tesztkérdés feldolgozása
7. 3 irreleváns kérdés tesztelése
8. Activity Logger és chunk linkek megtekintése

ELVÁRT EREDMÉNY:
✓ Minden relevans kérdéshez chunk hivatkozások
✓ Irreleváns kérdéseknél nincs chunk hivatkozás
✓ Activity Logger szín-kódozása helyes
✓ Performance: 2-5s per kérdés

TELJES TESZT IDŐTARTAMA: ~30-40 perc
```

---

**Legutolsó frissítés**: 2026. január 1.
