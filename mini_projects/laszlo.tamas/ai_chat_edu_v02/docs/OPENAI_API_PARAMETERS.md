# OpenAI API Paraméterek - GPT-4 Viselkedés Módosítása

**Utolsó frissítés**: 2026. január 2.

## 📋 Áttekintés

Ez a dokumentum összefoglalja az OpenAI GPT-4 (GPT-4 Turbo/GPT-4o) API híváskor elérhető paramétereket, amelyekkel módosítható a modell viselkedése.

---

## 🎨 Kreativitás és Véletlenszerűség

### `temperature` (0.0 - 2.0)
- **Alapértelmezett**: 1.0 (OpenAI), 0.7 (projektünk)
- **Leírás**: Kimenet véletlenszerűségének mértéke
- **Értékek**:
  - `0.0` = Teljesen determinisztikus, mindig ugyanaz a válasz
  - `0.7` = Kiegyensúlyozott (ajánlott chat alkalmazásokhoz)
  - `1.0` = Közepes kreativitás
  - `2.0` = Nagyon kreatív, váratlan válaszok

**Használat**:
```python
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[...],
    temperature=0.7
)
```

### `top_p` (0.0 - 1.0)
- **Alapértelmezett**: 1.0
- **Leírás**: Nucleus sampling - alternatíva a temperature-höz
- **Működés**: Csak a legvalószínűbb tokenek használata (kumulatív valószínűség alapján)
- **Ajánlás**: Ne használd egyszerre a temperature-rel, válassz egyet!

**Példa**:
- `top_p=0.9`: A legvalószínűbb 90%-nyi tokenek közül választ

---

## 🔄 Ismétlés Kontroll

### `frequency_penalty` (-2.0 - 2.0)
- **Alapértelmezett**: 0.0
- **Leírás**: Csökkenti a már használt szavak ismétlődését
- **Működés**: A token eddigi előfordulási száma alapján büntet
- **Használat**:
  - `0.5` - `1.0`: Kevesebb ismétlés
  - `1.0` - `2.0`: Erősen kerüli az ismétléseket

### `presence_penalty` (-2.0 - 2.0)
- **Alapértelmezett**: 0.0
- **Leírás**: Ösztönzi új témák bevezetését
- **Működés**: Ha egy token már előfordult (bármilyen gyakran), büntetés
- **Különbség**: Frequency figyelembe veszi a **mennyiséget**, presence csak a **tényt**

**Példa kombinált használat**:
```python
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[...],
    frequency_penalty=0.5,  # Csökkenti az ismétléseket
    presence_penalty=0.6    # Új témák bevezetése
)
```

---

## 📏 Kimenet Korlátok

### `max_tokens`
- **Alapértelmezett**: Nincs (model maximum)
- **Leírás**: Maximális generált tokenek száma
- **Figyelem**: Input + output összesen ne lépje túl a modell context windowját
  - GPT-4: 8192 token
  - GPT-4 Turbo: 128000 token
  - GPT-4o: 128000 token

### `stop`
- **Típus**: String vagy string lista
- **Leírás**: Stop szekvenciák, ahol a generálás megáll
- **Példa**:
```python
stop=["\n", "User:", "###"]  # Megáll ezek valamelyikénél
```

---

## 🔧 Strukturált Kimenet

### `response_format`
- **Lehetőségek**: `{"type": "text"}` (alapértelmezett) vagy `{"type": "json_object"}`
- **JSON mód követelménye**: System prompt tartalmazza a "JSON" szót
- **Használat**:
```python
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Return response as JSON"},
        {"role": "user", "content": "Extract name and age"}
    ],
    response_format={"type": "json_object"}
)
```

### `seed` (kísérleti)
- **Típus**: Integer
- **Leírás**: Determinisztikus output biztosítása
- **Figyelem**: Nem 100% garantált, de közel azonos válaszokat ad

---

## 🛠️ Function Calling / Tools

### `tools`
- **Típus**: Lista objektumokból
- **Leírás**: Elérhető függvények/toolok definiálása
- **Formátum**: JSON Schema alapú leírás

**Példa**:
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]
```

### `tool_choice`
- **Lehetőségek**: 
  - `"auto"` (alapértelmezett): Model dönt
  - `"none"`: Nem hívhat függvényt
  - `{"type": "function", "function": {"name": "konkrét_függvény"}}`: Kényszerít egy konkrét tool-t

---

## 📊 Egyéb Paraméterek

### `n`
- **Alapértelmezett**: 1
- **Leírás**: Hány alternatív választ generáljon párhuzamosan
- **Figyelem**: Költséghatékonyság! `n=3` = 3x token használat

### `stream`
- **Típus**: Boolean
- **Leírás**: Streaming kimenet (chunk-onként érkeznek a tokenek)
- **Használat**: Real-time UX élmény (pl. ChatGPT-szerű gépelés effekt)

```python
stream = openai.chat.completions.create(
    model="gpt-4",
    messages=[...],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

### `logprobs`
- **Típus**: Boolean vagy integer
- **Leírás**: Token-level valószínűségek visszaadása
- **Használat**: Debug, analízis, modell bizonytalanságának mérése

---

## 🎯 Projekt-Specifikus Konfiguráció

Az `ai_chat_edu_v02` projektben:

**Fájl**: `backend/config/system.ini`
```ini
CHAT_TEMPERATURE=0.7
CHAT_MODEL=gpt-3.5-turbo  # vagy gpt-4o-mini
```

**Használat**: `services/unified_chat_workflow.py`
```python
llm = ChatOpenAI(
    model=self.model_name,
    temperature=self.temperature
)
```

---

## � Modell-Specifikus Különbségek

### ✅ Minden modellben elérhető paraméterek
Az alapvető paraméterek **azonosak** minden GPT modellben:
- `temperature`, `top_p`, `max_tokens`, `stop`
- `frequency_penalty`, `presence_penalty`
- `n`, `stream`

### 📊 Modell-függő funkciók

#### GPT-3.5-turbo
- ❌ **Nincs vision** (képfeldolgozás)
- ✅ **Function calling**: csak `gpt-3.5-turbo-1106+` verzióktól
- ✅ **JSON mode**: csak `gpt-3.5-turbo-1106+` verzióktól
- ✅ `seed`: újabb verziókban elérhető
- ⚠️ `logprobs`: korlátozott (max 5 alternatív token)
- **Context window**: 16K token (újabb verziók)
- **Költség**: Legolcsóbb, gyors

#### GPT-4o-mini
- ✅ **Vision támogatás** (képek értelmezése)
- ✅ **Function calling**: teljes támogatás
- ✅ **JSON mode**: teljes támogatás
- ✅ `seed`: elérhető
- ✅ `logprobs`: bővített verzió (max 20 alternatív token)
- **Context window**: 128K token
- **Költség**: Középkategória, kiegyensúlyozott ár/teljesítmény

#### GPT-4 / GPT-4 Turbo / GPT-4o
- ✅ Minden funkció teljes támogatással
- **Context window**: 128K token (Turbo/4o), 8K token (GPT-4)
- **Költség**: Legdrágább, legjobb minőség

### 🎯 Gyakorlati különbségek táblázat

| Funkció | GPT-3.5-turbo | GPT-4o-mini | GPT-4 Turbo/4o |
|---------|---------------|-------------|----------------|
| **Alapparaméterek** | ✅ | ✅ | ✅ |
| **Function calling** | ✅ (1106+) | ✅ | ✅ |
| **JSON mode** | ✅ (1106+) | ✅ | ✅ |
| **Vision** | ❌ | ✅ | ✅ |
| **Max context** | 16K | 128K | 128K |
| **Logprobs (max)** | 5 | 20 | 20 |
| **Relatív költség** | 1x | 5x | 20x |

**Projekt konfiguráció**: Az `ai_chat_edu_v02` projektben a `gpt-3.5-turbo` vagy `gpt-4o-mini` modellek mindkettő támogatják az összes jelenleg használt paramétert.

---

## �💡 Best Practices

1. **Temperature vs. Top_p**: Válassz egyet! Ne kombináldd őket.
2. **Determinisztikus output**: `temperature=0` + `seed` paraméter
3. **Kreatív írás**: `temperature=1.0-1.5` + `presence_penalty=0.6`
4. **Kód generálás**: `temperature=0.2` + `max_tokens` limitelve
5. **JSON output**: Mindig adj példát a system promptban + `response_format`
6. **Token költségek**: Figyelj a `max_tokens` és `n` paraméterre!

---

## 🔗 Kapcsolódó Dokumentumok

- [HIERARCHICAL_PROMPTS.md](HIERARCHICAL_PROMPTS.md) - Prompt hierarchia (Application → Tenant → User)
- [LANGGRAPH_WORKFLOWS.md](LANGGRAPH_WORKFLOWS.md) - LangGraph workflow architektúra
- `backend/config/system.ini` - Aktuális konfiguráció

---

## 📚 Források

- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat/create)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/gpt-best-practices)
