# 🧪 TESZTEK - Test Suite Documentation

Ez a mappa az **RAG Agent alkalmazás** tesztelésével kapcsolatos fájlokat tartalmazza.

---

## 📊 Teszt Fájlok Áttekintése

### ✅ Teljes Körű Test Suite (9 Teszt)

#### CORE TESZTEK (5)

#### 1. **test_activity_logging.py** (80 sorok)
**Tesztelés:** Activity Logger funkciók  
**Mit csinál:**
- Dokumentum feltöltést végez
- 20 másodpercig monitorozza az Activity Logger panelt
- Az összes háttérfolyamat-event nyomon követésére tesztel
- Valós idejű activity API (`/api/activities`) meghívásait tesztel

**Futtatás:**
```bash
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw
python3 TESZTEK/test_activity_logging.py
```

**Várható eredmény:** ✅ 
- 20+ activity event megjelenik
- Hasonlóság típusok (info, processing, success, error)
- Timestamp-ek helyesen jelennek meg

---

#### 2. **test-activity.py** (188 sorok)
**Tesztelés:** Activity Logger rendszer teljes pipeline-je  
**Mit csinál:**
- Dokumentum feltöltést végez
- Activity logokat gyűjt az upload során
- Ellenőrzi az event szekvenciát
- Verifikálja az Activity Logger panel frissülését

**Futtatás:**
```bash
python3 TESZTEK/test-activity.py
```

**Várható eredmény:** ✅
- Teljes upload pipeline megjelenik az Activity Loggerben:
  - 📄 Dokumentum feldolgozása
  - 📖 Szöveg kinyerése
  - ✂️ Chunkolás
  - 🔗 Embedding generálása
  - 📊 Vektor-indexelés
  - ✅ Feltöltés kész

---

#### 3. **test_fallback.py** (64 sorok)
**Tesztelés:** Fallback keresés funkciók  
**Mit csinál:**
- Két kategória létrehozása (AI, Python)
- Dokumentumot csak Python kategóriához tölt fel
- AI kategóriás kérdést küld (ahol nincs dokumentum)
- Ellenőrzi, hogy fallback keresés aktiválódik-e

**Futtatás:**
```bash
python3 TESZTEK/test_fallback.py
```

**Várható eredmény:** ✅
- Ha dokumentum nincs az elsődleges kategóriában:
  - ⚠️ Fallback keresés aktiválódik
  - Az összes kategóriában keres
  - Ha sehol nincs (< 0.6 hasonlóság): "Dokumentumok nem tartalmaznak..." üzenet

---

#### 4. **test_similarity_threshold.py** (64 sorok)
**Tesztelés:** 0.6 hasonlósági küszöb funkciók  
**Mit csinál:**
- ChromaDB-ből lekéri az elérhető kollekciókat
- Irreleváns kérdéseket küld (pl. "Mi India fővárosa?")
- Ellenőrzi, hogy alacsony hasonlóság (< 0.6) esetén nincs chunk visszaadva

**Futtatás:**
```bash
python3 TESZTEK/test_similarity_threshold.py
```

**Várható eredmény:** ✅
- Irreleváns kérdésekre: "NO DOCUMENTS FOUND"
- Küszöb szűrés helyesen működik
- Az LLM szabad tudásból válaszol (nem dokumentumokból)

---

#### 5. **test_comprehensive.py** (113 sorok)
**Tesztelés:** Komprehenzív fallback keresés szcenáriók  
**Mit csinál:**
- AI és Python kategóriák leírásainak mentése
- Dokumentumok feltöltése mindkét kategóriához
- 4 teszt szcenárió futtatása:
  - Kérdés az AI kategóriához (docs léteznek)
  - Kérdés a Python kategóriához (docs léteznek)
  - AI kérdés Python kategóriához (fallback)
  - Vegyes kérdés (fallback)

**Futtatás:**
```bash
python3 TESZTEK/test_comprehensive.py
```

**Várható eredmény:** ✅
- Mindkét kategóriában találatok
- Kategória-routing helyesen működik
- Fallback szcenáriók kezelése

---

#### ÚJ TESZTEK (4) - Teljes Körű Funkciók

#### 6. **test_session_management.py** (Új) ⭐
**Tesztelés:** Chat előzmények és session kezelés  
**Mit csinál:**
- Session létrehozása
- Chat üzenetek tárolása
- Session előzmények lekérdezése
- Több session ugyanarra a felhasználóra
- Adatperzisztencia ellenőrzése (JSON fájlok)

**Futtatás:**
```bash
python3 TESZTEK/test_session_management.py
```

**Várható eredmény:** ✅
- Session fájl létrehozódik: `data/sessions/{user_id}_{session_id}.json`
- Összes üzenet mentésre kerül
- Helyes JSON struktúra (user_id, session_id, created_at, messages)

---

#### 7. **test_data_persistence.py** (Új) ⭐
**Tesztelés:** Teljes adatperzisztencia  
**Mit csinál:**
- User profil ellenőrzése (`data/users/*.json`)
- Session fájlok validálása (`data/sessions/*.json`)
- Chunks.json struktúra verifikálása
- ChromaDB index ellenőrzése
- Feltöltött fájlok persistenciájának tesztelése

**Futtatás:**
```bash
python3 TESZTEK/test_data_persistence.py
```

**Várható eredmény:** ✅
- User profil: `username, categories, created_at, preferences`
- Session: `user_id, session_id, messages, created_at`
- Chunks: `id, text, embedding, metadata`
- ChromaDB: Elérhető és működő

---

#### 8. **test_error_handling.py** (Új) ⭐
**Tesztelés:** Hibakezelés és edge case-ek  
**Mit csinál:**
- Hiányzó paraméterek tesztelése
- Érvénytelen inputok tesztelése
- Üres fájlok feltöltésének tesztelése
- SQL/XSS injection próbálkozások
- Nem létező recursos kezelése
- Nagy inputok (10000 karakter)
- API endpoint elérhetőség

**Futtatás:**
```bash
python3 TESZTEK/test_error_handling.py
```

**Várható eredmény:** ✅
- Invalid input: `status 400/422`
- Empty file: `status 400`
- Missing params: `status 400`
- XSS/SQL: `sanitized/rejected`
- Endpoints: `all accessible (200/400-range)`

---

#### 9. **test_category_management.py** (Új) ⭐
**Tesztelés:** Kategória menedzsment teljes pipeline-je  
**Mit csinál:**
- Kategóriák létrehozása
- Leírások mentése & lekérdezése
- Dokumentumok feltöltése kategóriákhoz
- Category-document asszociációk verifikálása
- User profil kategória tárolása
- LLM kategória routing tesztelése
- Kategória statisztikák

**Futtatás:**
```bash
python3 TESZTEK/test_category_management.py
```

**Várható eredmény:** ✅
- Kategóriák létrehozódnak user profilban
- Leírások mentésre & lekérdezhetők
- Dokumentumok indexálódnak kategóriánként
- LLM routing helyesen működik
- Chunks asszociálódnak kategóriához

---

### 📄 Támogatás Dokumentáció

#### **test_rag.md**
**Tartalom:** Demo dokumentum AI kategóriához  
**Használat:** Teszteléshez (DEMO_files_for_testing mappában is)

---

## 🎯 Ajánlott Tesztelési Sorrend

### Lépésről Lépésre Futtatás

```bash
# 1. Szerver indítása (az al-mappában)
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw
source .env && ./start-dev.sh

# 2. Új terminálban a tesztek futtatása (ebben a sorrendben):

# CORE TESZTEK (5)
python3 TESZTEK/test_activity_logging.py        # ~1 min - Activity Logger alapok
python3 TESZTEK/test_comprehensive.py           # ~2 min - Kategória routing + fallback
python3 TESZTEK/test_fallback.py                # ~1 min - Fallback keresés
python3 TESZTEK/test_similarity_threshold.py    # ~1 min - Hasonlóság szűrés
python3 TESZTEK/test-activity.py                # ~2 min - Teljes pipeline

# ÚJ TESZTEK (4)
python3 TESZTEK/test_session_management.py      # ~1 min - Chat előzmények
python3 TESZTEK/test_category_management.py     # ~1 min - Kategória menedzsment
python3 TESZTEK/test_data_persistence.py        # ~1 min - Adattárolás
python3 TESZTEK/test_error_handling.py          # ~1 min - Hibakezelés
```

**Teljes teszt időtartam:** ~10-15 perc (az összes 9 teszt szerint)

---

---

## 🔧 Hogyan Működnek a Tesztek?

### A Teszt Végrehajtási Folyamat

#### 1️⃣ **Inicializálás**
```python
# Minden teszt így indul:
import requests

BASE_URL = "http://localhost:8000"
user_id = "test_user"
session_id = "test_session_123"

# API kérés: User név lekérése az OS-ból
response = requests.post(f"{BASE_URL}/api/get-user")
user_id = response.json().get("user_id")
```

#### 2️⃣ **Kategória Feltöltés**
```python
# Kategória + leírás mentése az LLM-be
response = requests.post(
    f"{BASE_URL}/api/desc-save",
    json={
        "user_id": user_id,
        "category": "AI",
        "description": "Mesterséges Intelligencia és gépi tanulás..."
    }
)
# ✅ status 200: kategória mentésre kerül az user profilban
```

#### 3️⃣ **Dokumentum Feltöltés**
```python
# Fájl feltöltése az adott kategóriához
with open("demo_file.md", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/upload",
        files={"file": f},
        data={"user_id": user_id, "category": "AI"}
    )
# ✅ status 200: fájl feldolgozódik
#   - Szöveg kinyerés
#   - Chunkolás
#   - Embedding generálás (OpenAI API)
#   - ChromaDB indexálás
```

#### 4️⃣ **Activity Logger Polling** (csak test_activity_logging.py-ban)
```python
# Az upload közben monitorozzuk a háttérfolyamatokat
for i in range(20):  # 20 másodperc
    response = requests.get(
        f"{BASE_URL}/api/activities",
        params={"user_id": user_id}
    )
    activities = response.json()
    # Megjelennek az events:
    # 📄 Dokumentum feldolgozása
    # 📖 Szöveg kinyerése
    # ✂️ Chunkolás
    # 🔗 Embedding generálása
    # 📊 ChromaDB indexálása
    # ✅ Feltöltés kész
    time.sleep(1)
```

#### 5️⃣ **Keresési Kérdés**
```python
# Keresési API meghívása
response = requests.post(
    f"{BASE_URL}/api/search-query",
    json={
        "user_id": user_id,
        "category": "AI",
        "session_id": session_id,
        "message": "Mi a mesterséges intelligencia?"
    }
)
# ✅ status 200: RAG pipeline futtat
#   1. Kategória routing (AI vagy nem?)
#   2. ChromaDB keresés (hasonlóság > 0.6?)
#   3. Fallback keresés (nincs találat → összes kategóriában)
#   4. LLM válasz generálása (dokumentum-alapú)
#   5. Chunk hivatkozások mentése
```

#### 6️⃣ **Adatperzisztencia Ellenőrzés** (test_data_persistence.py)
```python
# Fájl-alapú storage verifikálása
import json
import os

# User profil: data/users/{user_id}.json
with open(f"data/users/{user_id}.json") as f:
    user_data = json.load(f)
    assert "categories" in user_data  # Kategóriák mentve?
    assert "created_at" in user_data

# Session chat előzmények: data/sessions/{user_id}_{session_id}.json
with open(f"data/sessions/{user_id}_{session_id}.json") as f:
    session_data = json.load(f)
    assert len(session_data["messages"]) > 0  # Üzenetek mentve?

# ChromaDB vektor indexek: data/chroma_db/
assert os.path.exists("data/chroma_db/")  # ChromaDB mappa létezik?
```

#### 7️⃣ **Hibakezelés Ellenőrzés** (test_error_handling.py)
```python
# Érvénytelen input kezelése
response = requests.post(
    f"{BASE_URL}/api/search-query",
    json={"user_id": "", "message": ""}  # Hiányzó paraméterek
)
assert response.status_code == 400  # ✅ Helyes: error response

# XSS injection szűrés
response = requests.post(
    f"{BASE_URL}/api/search-query",
    json={
        "user_id": "test_user",
        "message": "<script>alert('XSS')</script>"
    }
)
# ✅ A scripttag eltávolítódik, biztonságosan kezelésre kerül
```

---

### ✨ Mit Tesztelt Minden Teszt

| Teszt | Ellenőrzés | Kimenet |
|-------|-----------|---------|
| **test_activity_logging.py** | Activity Logger polling | 20+ event, valós idő |
| **test_comprehensive.py** | Kategória routing + fallback | Helyes kategóriaszelekció |
| **test_fallback.py** | Fallback keresés aktiválása | Kategóriaváltás működik |
| **test_similarity_threshold.py** | 0.6 hasonlósági küszöb | Alacsony relevancia szűrés |
| **test-activity.py** | Teljes upload pipeline | Event szekvencia OK |
| **test_session_management.py** | Chat előzmények tárolása | JSON fájlok létrehozódnak |
| **test_category_management.py** | Kategória életciklusa | Routing + leírások OK |
| **test_data_persistence.py** | Adattárolás integritása | User, session, chunks OK |
| **test_error_handling.py** | Hibakezelés & input szűrés | 400-as hibakódok, sanitizálás |

---

## 🔍 Hibakeresési Útmutató

### Gyakori Problémák és Megoldások

#### ❌ **"Connection refused" hiba**
```
Error: Failed to establish a connection (Connection refused)
```
**Megoldás:**
```bash
# Ellenőrizd, hogy a szerver fut-e:
ps aux | grep start-dev.sh

# Ha nem fut, indítsd el:
cd /Users/tothgabor/ai-agents-hu/mini_projects/gabor.toth/2_hw
source .env && ./start-dev.sh
```

#### ❌ **"OpenAI API key error"**
```
Error: OpenAI API key not found
```
**Megoldás:**
```bash
# Ellenőrizd az .env fájlt:
cat .env

# Ha hiányzik az OPENAI_API_KEY:
export OPENAI_API_KEY="sk-..."
source .env
./start-dev.sh
```

#### ❌ **"ChromaDB not found"**
```
Error: data/chroma_db directory not found
```
**Megoldás:**
```bash
# Az app automatikusan létrehozza, de kézileg is:
mkdir -p data/chroma_db

# Vagy az upload után automatikusan létrehozódik
python3 TESZTEK/test_activity_logging.py
```

#### ❌ **"Session file not created"**
```
Error: data/sessions/test_user_session_123.json not found
```
**Megoldás:**
```bash
# Ellenőrizd, hogy az API válaszol-e:
curl http://localhost:8000/api/search-query -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"test","category":"test"}'

# Az első kérdés után létre kell jönnie a session file-nak
python3 TESZTEK/test_session_management.py
```

#### ✅ **Sikeres Teszt Teljesítés Jelei**
```python
# Activity Logger megjelen (test_activity_logging.py):
✅ Retrieved 23 activities
✅ Event types: ['processing', 'success', 'info']
✅ Timestamps validated

# Session mentésre kerül (test_session_management.py):
✅ Session created successfully
✅ Session file path: data/sessions/test_user_test_session.json
✅ Messages stored: 2

# Adatperzisztencia OK (test_data_persistence.py):
✅ User profile validation passed
✅ Session files validation passed
✅ Chunks.json validation passed
✅ ChromaDB validation passed
```

---

## 📝 Jelenlegi Projekt Status

### ✅ Teljes körűen Tesztelt Funkciók

- **Activity Logger** - Valós idejű háttérfolyamat naplózás
- **Dokumentum Feltöltés** - Markdown, PDF, DOCX támogatás
- **Kategória Routing** - LLM alapú intelligens kategóriaválasztás
- **Vektor Keresés** - ChromaDB + OpenAI embedding
- **Fallback Keresés** - Kategóriaváltás, amikor nincs találat
- **Hasonlóság Szűrés** - 0.6 küszöb irreleváns dokumentumokhoz
- **RAG Válasz Generálás** - Dokumentum-alapú LLM válaszok
- **Chunk Hivatkozások** - Kattintható modal panelok
- **Activity API** - `/api/activities` endpoint (1s polling)

---

## 🚀 További Fejlesztési Irányok (Nem Szükséges)

Ha később szükséges:
- Integration tesztek (pytest / unittest)
- Performance tesztek (latency, throughput)
- Load tesztek (sok párhuzamos kérdés)
- Frontend E2E tesztek (Cypress / Playwright)
- API integráció tesztek (OpenAI, ChromaDB mockkal)

---

**Legutolsó frissítés**: 2026. január 1.
