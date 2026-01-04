# KnowledgeRouter – Baseline (Szent Grál) v0.6

**Cél:** valós HR+IT igények kezelése egy agenttel úgy, hogy a vizsgán **demózható, működő** legyen, és technikailag teljesítse a **MINI_PROJECTS** elvárásait (routing, multi-domain, multi-vector, RAG+citációk, action/tool, LangGraph, mérhetőség, tervezés).

## Changelog


### v0.5 → v0.6 (csiszolás, funkcióbővítés nélkül)
- `DONE` vs `CLOSED` jelentés és life-cycle pontosítva (request szint).
- Retrieval `min_score` kezelés pontosítva: **kalibráció** + score metrikák logolása (hogy a threshold ne “vakon” legyen).
- Citáció validátor: “bekezdés” definíció rögzítve (`\n\n` szeparátor), így implementációban nincs vita/edge-case.
- Quality Gate: `requests.type` **MVP enum** + típusonkénti `required_fields` mapping táblázat.
- Opcionális enrichment (Nominatim): User-Agent + cache (TTL) + fail-open viselkedés leírva.

### v0.4 → v0.5
- Státusz enumok egységesítve: `requests.status` és API `status` ugyanaz (nincs `ASSIGNED` a requestben; ez task szint).
- `/ask` vs `/intake` határ tisztázva: `/ask` stateless (nincs DB, nincs action), `/intake` mindig requestet nyit/persistál.
- Retrieval policy konkretizálva: `top_k` + `min_score` threshold + `NO_KB_HIT` döntési szabály.
- `validate_output` retry policy pontosítva: `validation_fail_reason` audit + retry utáni safe fallback.
- `action_key` stabilizálás: canonical JSON payload definíció (kulcsrendezés + whitespace eliminálás).
- `/updates` integritás: konkrét HMAC header-ek és ellenőrzési lépések (demo-ban kapcsolható).

### v0.3 → v0.4
- Output schema pontosítva: `resolution` + kötelező példák (NEEDS_INFO, DENIED, SELF_SERVICE_OK, ACTION_DISPATCHED, NO_KB_HIT).
- Routing determinisztika: rules-first fallback + LLM router csak akkor, ha a szabályok nem döntöttek (audit reason kötelező).
- RAG ingest demó-szintre konkretizálva: minimum KB dataset + forrásfájl struktúra + chunk/metadata konvenció.
- Citáció szabály szigorítva: ha van retrieval, **minden bekezdés** kap citációt; ha nincs, kötelező “nincs elég adat” sablon és `citations=[]`.
- Action idempotencia: `action_key` + Action Sink idempotency viselkedés (duplikált POST → ugyanaz az `external_id`).
- Memory scope konkretizálva: pontos “hydrate” mezők + history limit.

### v0.2 → v0.3
- LangGraph flow bővítve: `policy_check` és `validate_output` explicit node.
- Memory: visszatöltés DB-ből `request_key` alapján + folytató endpoint.
- Valós action demó: Action Sink service.
- Citáció formátum egységesítve: `[CIT-x]` + `citations[]`.
- Routing fallback: `general/unknown` determinisztikus ág.

---

## 0) Alapelv: MINI_PROJECTS-kompatibilitás, de valós üzlet
- Nem másolat. **Ekvivalens technikai megoldás** valós céges problémára.
- A “multi-domain” nálunk **valós funkcionális domainek**:
  - **HR** (on/offboarding, HR self-service)
  - **Compliance / IBF** (jóváhagyások, access policy)
  - **IT Support** (L1–L3 sub-route)
  - **Operations / Infra** (beszerzés, erőforrás, eszkaláció)
  - **General/Unknown** (fallback, tisztázás)
- **EndUser** nem domain, hanem fő **input csatorna** (incident, kérdés, panasz).

**Vizsga-demóban kötelezően látszik:**
1) route/döntés (domain + IT sub-route),
2) RAG + **citációk**,
3) legalább 1 **action** (valós HTTP POST egy működő service-nek),
4) LangGraph flow,
5) minimál audit + metrika,
6) output schema következetes JSON formában.

---

## 1) Üzleti probléma és célok

### Probléma
- Fragmentált IT működés, sokszereplős folyamat.
- Bejövő kérések **hiányosak**, rossz címzett, nincs konzisztens tracking.
- SLA csúszás, nincs automatizált follow-up.
- EndUser incidentek (a kérések nagy része) gyenge minőségű ticketben landolnak.

### Cél
A KnowledgeRouter (KR) legyen a központi belépési pont:
- **intake** → **enrichment (opcionális)** → **quality gate** → **routing** → **policy check** → **RAG** → **action dispatch** → **tracking** → **SLA follow-up** → **closure**
- Self-service kérdéseknél: **RAG válasz citációval**, ticket nélkül.

---

## 2) Szereplők és csatornák

### Csatornák (input source)
- **EndUser channel:** incidentek, IT kérdések, “nem megy X”.
- **HR channel:** onboarding/offboarding/access indítás.
- **Internal channel:** státusz update-ek (L1/L2/L3/IBF/Infra visszajelez).

### Szervezeti szereplők (target csapatok)
- **HR**
- **IBF / Compliance**
- **IT Support:** L1 Desktop, L2 Directory, L3 Network/VPN
- **Infra/Operations**
- **KR rendszer**

---

## 3) Domain modell (routing cél)

### Domain: HR
- Scope: onboarding/offboarding, HR self-service (pl. szabadság “hogyan?”).
- Knowledge: HR policy/SOP.
- Action: HR task/értesítés, checklist, státusz.

### Domain: Compliance / IBF
- Scope: access approval, least privilege, audit trail.
- Knowledge: access policy, approval rules.
- Action: approval request létrehozás / döntés kérése (mock action).

### Domain: IT Support
- Scope: incident + IT szolgáltatás kérések.
- Knowledge: runbook/troubleshooting SOP.
- **Sub-route:** `it_l1 | it_l2 | it_l3` (ticket típustól függ).
- Action: ticket dispatch a megfelelő sub-route-nak.

### Domain: Operations / Infra
- Scope: beszerzés, erőforrás, eszkaláció, change jellegű ügyek.
- Knowledge: procurement / ops SOP.
- Action: procurement/escalation action.

### Domain: General/Unknown (fallback)
- Scope: nem egyértelmű igény / kevés adat.
- Knowledge: “triage” guideline.
- Action: alapból **nincs**; célzott kérdések (quality gate), majd újrarouting.

---

## 4) Funkcionális baseline (MVP → bővíthető)

### 4.1 Intake és normalizálás
- Input: szabad szöveg + opcionális meta (ki, hol, mikor), vagy strukturált JSON.
- Output: normalizált “request draft” (Pydantic schema).

### 4.2 Public API Enrichment Tool (HF1-kompatibilitás)
Cél: legyen **valós publikus API hívás**, ami a végső projektben is értelmes.
- Példa: **Nominatim (OpenStreetMap)** geokódolás a `location/office` mező normalizálásához (onboarding, site routing).
  - Kötelező `User-Agent` header (Nominatim policy miatt).
  - Cache: egyszerű LRU/mem cache vagy SQLite cache, **TTL=24h**.
  - Fail-open: rate-limit/hiba esetén enrichment skip, a request nem bukhat el (event: `enrichment_skipped`).
- Input: `location_text` (pl. “Budapest”, “Frankfurt”)
- Output: `lat/lon`, `display_name`, opcionálisan `country`
- Ha sikertelen: enrichment kihagyható, nem blokkol.

> HF1-ben ez lehet az első “public API call” + mellé a “valós action” a sink felé.

### 4.3 Quality Gate (minőségbiztosítás)

**Cél:** ne menjen ki action / végleges válasz hiányos ticketből.  
**Alapelv:** request `type` → kötelező mezők (`required_fields`) → hiány (`missing_fields`) → célzott kérdések.

#### 4.3.1 Request type (MVP enum)
A `requests.type` mező **kötelező**, az alábbi (MVP) értékekkel:
- `hr_onboarding` | `hr_offboarding` | `hr_question`
- `access_request` | `compliance_question`
- `it_incident` | `it_howto`
- `ops_procurement`
- `general_question`

#### 4.3.2 Required fields mapping (MVP)
| type | required_fields (min.) | megjegyzés |
|---|---|---|
| `hr_onboarding` | `employee_name`, `start_date`, `location_or_office` | location mehet raw, enrichment opcionális |
| `hr_offboarding` | `employee_name`, `end_date`, `manager_or_owner` | |
| `hr_question` | `question` | self-service |
| `access_request` | `user`, `system`, `role_requested` | compliance domain, approval action |
| `compliance_question` | `question` | self-service |
| `it_incident` | `affected_service`, `impact`, `contact` | IT routing + ticket action |
| `it_howto` | `question` | tipikusan RAG |
| `ops_procurement` | `item`, `quantity`, `business_justification` | ops stub is lehet |
| `general_question` | `question` | fallback |

#### 4.3.3 Viselkedés hiány esetén
- `status=NEEDS_INFO`
- `resolution=NEEDS_INFO`
- `questions[]` célzottan a `missing_fields` alapján (max 3-5 kérdés)
- `payload`-ba írjuk:
  - `required_fields`, `missing_fields`, `answers_so_far`
- Turn-based kitöltés: min. 1 kör elég demóra (UI/CLI vagy `/requests/{request_key}/messages`).


### 4.4 Routing (domain + sub-route)

**Cél:** ismételhető, auditálható routing.  
**Elv:** először determinisztikus szabályok, csak utána LLM-alapú osztályozás.

#### 4.4.1 Rules-first routing (MVP)
1) **Hard rules (felülírhatatlan)**
- `channel=internal` + `/updates` → *internal update* (nem domain routing).
- Ha `role` tiltott egy domainre → *policy_check* fogja, de routing indoklásban jelöljük.

2) **Keyword/pattern routing (confidence alapú)**
- HR (példák): `szabadság`, `onboarding`, `offboarding`, `belépés`, `kilépés`
- Compliance/IBF (példák): `hozzáférés`, `access`, `jogosultság`, `approval`, `audit`, `least privilege`
- IT (példák): `vpn`, `nyomtató`, `wifi`, `jelszó`, `hiba`, hex hibakód (`0x...`)
- Ops/Infra (példák): `beszerzés`, `procurement`, `purchase`, `escalation`, `change`

**Tie-break:**
- “access/jogosultság/approval” → **compliance** prior (még ha IT szavak is vannak).
- “beszerzés/purchase” → **ops** prior.

#### 4.4.2 IT sub-route (L1/L2/L3)
- **it_l3:** network/VPN (`vpn`, `network`, `wifi`, “nem csatlakozik”, route, DNS)
- **it_l2:** account/directory (`AD`, `account`, `groups`, `permission`, “nem tudok belépni”)
- **it_l1:** minden más default (desktop/app jelleg)

#### 4.4.3 LLM routing (csak ha a szabályok nem döntöttek)
Ha rules-first eredménye `unknown` vagy alacsony confidence:
- LLM router **kötött JSON** választ ad:
  - `domain`, `sub_route`, `confidence` (0–1), `reason`
- Ha `confidence < 0.6` → fallback: `general`.

**Audit kötelező mezők:**
- `routing.method = rules|llm|fallback`
- `routing.reason`
- `routing.keywords_hit[]` (ha rules)

---

### 4.5 Policy Check / Guardrails
A routing és RAG előtt kötelező ellenőrzés:
- RBAC/ACL: a kérdező `role` jogosult-e a domain/kb elérésre.
- PII: logba csak maszkolt mezők kerüljenek.
- Prompt injection: külső utasítás nem írhatja felül a retrieval policy-t.

Ha bukik: `status=DENIED` vagy `NEEDS_INFO` (attól függően, hogy jogosultság vs hiányos adat).

### 4.6 RAG + citációk
- Policy/runbook alapján válaszol:
  - self-service esetben: usernek válasz ticket nélkül,
  - workflow esetben: decision support + checklist + required fields.
- Citáció formátum: `[CIT-1] [CIT-2]` + `citations[]` objektumok.

### 4.7 Workflow Action (tool)
- Legalább 1 action **mindig valós HTTP hívás**.
- MVP-ben külső rendszerek helyett **Action Sink** (lásd lent).
- Action eredmény: `external_id` + raw response tárolás.

#### 4.7.1 Idempotencia (kötelező)
Az action dispatch **idempotens** legyen (graph retry / user “küldd újra” ne duplikáljon).
- `action_key` = determinisztikus hash (pl. `sha256(request_key + action_type + canonical_payload)`).
- **Canonical payload (stabil hash):**
  - `canonical_payload` = JSON kanonizálás (kulcsrendezés + whitespace eliminálás), és **nem** tartalmazhat illékony mezőket (pl. timestamp, trace_id).
  - Minta (nyelvfüggetlen elv): `json.dumps(payload, sort_keys=True, separators=(",", ":"))`

- KR → Action Sink: küldje el az `action_key`-t:
  - body mezőként (`action_key`), **és/vagy**
  - `Idempotency-Key` headerként.

Elvárt viselkedés:
- Ugyanazzal az `action_key`-val érkező POST → **ugyanazt** az `external_id`-t adja vissza.

---

### 4.8 Tracking, SLA, follow-up
- Request + Task státusz DB-ben.
- SLA tick: overdue esetén reminder, majd escalation (Action Sink csatornákon).

### 4.9 Státusz update fogadás
- Internal channel webhook: task/request státusz frissítés.
- Idempotens update (duplikált event ne borítson).

### 4.10 Output validálás (JSON schema + citáció)

**Kanonikus response objektum (minden endpoint):**
- `request_key` *(string|null)*: **csak** `/ask` esetén lehet `null`. Minden stateful flow (`/intake`, `/requests/{request_key}/messages`) **mindig** ad `request_key`-t.
- `domain` *(hr|compliance|it|ops|general)* + `sub_route?`
- `status` *(NEW|NEEDS_INFO|IN_PROGRESS|WAITING|DONE|CLOSED|DENIED)*
  - `DONE`: a KR szerint a munka **elkészült** (válasz megadva és/vagy action dispatch megtörtént), de a request még élhet (pl. belső update/confirm miatt).
  - `CLOSED`: **terminális** lezárás, nem várunk további lépést. Új igény = új request (új `request_key`).
- `resolution` *(NEEDS_INFO|DENIED|SELF_SERVICE_OK|ACTION_DISPATCHED|NO_KB_HIT|STATUS)*: az aktuális futás kimenete
- `questions[]` *(string[]|[])*: csak NEEDS_INFO esetben nem üres
- `answer` *(string|null)*
- `citations[]` *(object[]|[])*: `[CIT-x]` ↔ chunk mapping
- `workflow` *(object|null)*: action esetben részletek
- `metrics` *(object)*: `latency_ms`, `retrieved_k`, `action_success`, stb.

**Citáció szabály (szigorú, validate_output enforce):**
1) Ha `retrieved_k > 0` és `answer != null`:
   - `citations[]` **nem lehet üres**.
   - Az `answer` **minden bekezdésében** legyen legalább 1 `[CIT-x]`.
   - `citations[].cit_id` pontosan a szövegben használt `CIT-x`-ekre hivatkozzon.
2) Ha `retrieved_k == 0`:
   - `citations=[]`
   - `answer` legyen rövid “nincs elég adat a tudásbázisban” sablon (hallucináció stop)
   - `resolution=NO_KB_HIT`

**Schema enforcement:**
- Pydantic model + explicit enumok.
- Hibás output → `validate_output` node:
  - vagy újragenerál (1 retry),
  - vagy “safe fallback” (NO_KB_HIT / NEEDS_INFO).

---

## 5) Architektúra

### 5.1 Komponensek
1) **KR Orchestrator (FastAPI)**
- REST API (intake, ask, status, message continuation)
- LangGraph workflow engine
- LLM adapter (OpenAI API, backendből)
- RAG retriever (Qdrant)
- DB réteg (Postgres)
- Scheduler (APScheduler)

2) **Action Sink Service (FastAPI, kicsi konténer)**
- Demo cél: “külső integráció” szimuláció
- Beérkező action POST-okat **tartósan eltárolja** és listázhatóvá teszi

3) **PostgreSQL**
- users/requests/tasks/events/documents (+ opcionális messages)

4) **Qdrant (Vector DB)**
- domainenként külön collection / namespace

### 5.2 Kommunikáció
- KR UI/CLI → KR Orchestrator: HTTPS JSON
- KR Orchestrator → Postgres: SQL
- KR Orchestrator → Qdrant: HTTP
- KR Orchestrator → Action Sink: HTTP POST
- Internal update → KR Orchestrator: HTTP POST
- KR Orchestrator → Public API (enrichment): HTTP GET (opcionális)

---

## 6) Memory modell (explicit)

**Memory definíció:** a KR képes több turn-ön át ugyanahhoz a Request-hez kapcsolódni.

### 6.1 Azonosító
- `request_key` a “conversation handle”.

### 6.2 Hydrate scope (mit töltünk vissza DB-ből?)
`hydrate_state(request_key)` minimum:
- **requests**: `status`, `domain`, `type`, `payload` (benne: `required_fields`, `missing_fields`, `answers_so_far`, `last_resolution`)
- **tasks**: csak az aktív taskok (OPEN/WAITING/IN_PROGRESS/BLOCKED)
- **events**: utolsó N esemény (pl. 50) timeline-hoz
- **messages** *(ajánlott)*: utolsó N üzenet (pl. 20) – *csak a beszélgetéshez szükséges*
- **workflow mapping**: ha volt action, `external_id`, `action_key`

**Nem töltünk vissza** nagy/illékony mezőket:
- `retrieved_chunks` (újra-retrieve futásonként), max a legutóbbi `citations` marad auditban.

### 6.3 Folytatás endpoint
- Folytatás: `/requests/{request_key}/messages` endpointon.
- A beérkező új message után újra lefut a graph **ugyanazzal a request kontextussal** (hydrate → run → persist).

---

## 7) Data model (baseline)

### 7.1 Core táblák
**users**
- `id`, `full_name`, `email?`, `employment_status`, `department?`, `manager?`, `created_at`, `updated_at`

**requests**
- `id`, `request_key` (KR-YYYYMMDD-XXXXXX), `channel` (enduser/hr/internal), `domain`, `type`
- `status` (NEW/NEEDS_INFO/IN_PROGRESS/WAITING/DONE/CLOSED/DENIED)
  - `DONE` = elkészült, de még nem feltétlen lezárt.
  - `CLOSED` = végleges lezárás.
  - Megjegyzés: “ASSIGNED” **nem** request státusz; az assignment a `tasks.assignee` mezőben van.
- `payload` (JSONB), `created_at`, `last_activity_at`, `closed_at`

**tasks**
- `id`, `request_id`, `owner_domain`, `assignee` (IT_L1/IT_L2/IT_L3/HR/IBF/OPS)
- `status` (OPEN/WAITING/IN_PROGRESS/DONE/BLOCKED)
- `due_at`, `last_ping_at`, `notes` (JSONB)

**events** (audit)
- `id`, `request_id`, `ts`, `event_type`, `actor`, `data` (JSONB)

**documents** (opcionális)
- `id`, `request_id`, `filename`, `storage_path`, `extracted_text?`

**messages** (opcionális, de ajánlott a memory demonstrálásához)
- `id`, `request_id`, `sender` (user/hr/kr), `text`, `created_at`, `meta` (JSONB)

### 7.2 Vector metadata (Qdrant payload)
- `domain` (hr/compliance/it/ops/general)
- `doc_id`, `title`, `source`, `chunk_id`
- `acl_roles[]` (pl. HR only)
- `created_at`

---

## 8) Vector DB struktúra (multi-vector store)
- Collection per domain:
  - `kb_hr`
  - `kb_compliance`
  - `kb_it`
  - `kb_ops`
  - `kb_general` (triage/általános)
- (Opcionális) IT sub-route szerint további bontás:
  - `kb_it_l1`, `kb_it_l2`, `kb_it_l3`
  - MVP-ben elég `kb_it`.

---

## 9) API contract (kanonikus)

### 9.1 KR Orchestrator

#### 9.1.1 Response schema és státusz-jelentés
A KR minden endpointon a **kanonikus response objektumot** adja vissza (lásd 4.10).

**`status` (request állapot):**
- `NEW` / `IN_PROGRESS` / `WAITING` / `DONE` / `CLOSED`
- `NEEDS_INFO` (hiányos adat, kérdéslistával)
- `DENIED` (policy/RBAC tiltás)

**`resolution` (aktuális futás kimenete):**
- `NEEDS_INFO`: további adatok kellenek
- `DENIED`: jogosultsági/policy tiltás
- `SELF_SERVICE_OK`: usernek megválaszolható ticket nélkül (RAG+cit)
- `ACTION_DISPATCHED`: workflow action elküldve (Action Sink)
- `NO_KB_HIT`: nincs találat a KB-ben (hallucináció stop)
- `STATUS`: csak státuszinformáció (pl. GET /requests)

#### 9.1.2 Példa kimenetek (status + resolution)

**NEEDS_INFO (quality gate)**
```json
{
  "request_key": "KR-20251220-8F3K2D",
  "domain": "it",
  "sub_route": "it_l1",
  "status": "NEEDS_INFO",
  "resolution": "NEEDS_INFO",
  "questions": ["Milyen eszköz/OS?", "Pontosan mi a hibaüzenet?"],
  "answer": null,
  "citations": [],
  "workflow": null,
  "metrics": { "latency_ms": 820, "retrieved_k": 0, "action_success": false }
}
```

**DENIED (RBAC)**
```json
{
  "request_key": "KR-20251220-8F3K2D",
  "domain": "compliance",
  "sub_route": null,
  "status": "DENIED",
  "resolution": "DENIED",
  "questions": [],
  "answer": "Ehhez a témához nincs jogosultságod. Kérd a felettesed/IBF jóváhagyását.",
  "citations": [],
  "workflow": null,
  "metrics": { "latency_ms": 410, "retrieved_k": 0, "action_success": false }
}
```

**SELF_SERVICE_OK (RAG válasz, /ask példa)**
- Megjegyzés: ugyanaz a kimenet `/intake`-nál is lehet, csak ott `request_key` **nem** `null`.
```json
{
  "request_key": null,
  "domain": "hr",
  "sub_route": null,
  "status": "DONE",
  "resolution": "SELF_SERVICE_OK",
  "questions": [],
  "answer": "Szabadság igénylés: a HR portalon… [CIT-1]",
  "citations": [
    { "cit_id": "CIT-1", "doc_id": "HR-POL-001", "chunk_id": "HR-POL-001#003", "score": 0.82, "source": "kb_hr" }
  ],
  "workflow": null,
  "metrics": { "latency_ms": 930, "retrieved_k": 4, "action_success": false }
}
```

**ACTION_DISPATCHED (workflow)**
```json
{
  "request_key": "KR-20251220-8F3K2D",
  "domain": "it",
  "sub_route": "it_l2",
  "status": "IN_PROGRESS",
  "resolution": "ACTION_DISPATCHED",
  "questions": [],
  "answer": null,
  "citations": [],
  "workflow": {
    "action_type": "ticket",
    "action_key": "sha256:...",
    "external_id": "AS-8f2c3a",
    "channel": "ticket"
  },
  "metrics": { "latency_ms": 1200, "retrieved_k": 0, "action_success": true }
}
```

**NO_KB_HIT (nincs tudásbázis találat)**
```json
{
  "request_key": null,
  "domain": "general",
  "sub_route": null,
  "status": "DONE",
  "resolution": "NO_KB_HIT",
  "questions": [],
  "answer": "Nincs elég adat a tudásbázisban ehhez. Adj több részletet vagy nyiss ticketet.",
  "citations": [],
  "workflow": null,
  "metrics": { "latency_ms": 500, "retrieved_k": 0, "action_success": false }
}
```

**POST /intake** *(fő belépési pont)*
- **Stateful:** mindig hoz létre `request` rekordot és **persistál** (self-service esetén is).
- Self-service esetén is visszaad `request_key`-t, és tipikusan azonnal `status=DONE` → `CLOSED` (vagy maradhat `DONE` demóban).

- input:
```json
{
  "channel": "enduser|hr",
  "role": "enduser|hr|it|ibf|ops|admin",
  "text": "…",
  "meta": { "location": "Budapest", "attachments": [] }
}
```
- output (egységes):
```json
{
  "request_key": "KR-20251220-8F3K2D",
  "domain": "it",
  "sub_route": "it_l1",
  "status": "NEEDS_INFO",
  "resolution": "NEEDS_INFO",
  "questions": ["Milyen hibaüzenet?", "Küldj screenshotot."],
  "answer": null,
  "citations": [],
  "workflow": null,
  "metrics": { "latency_ms": 1234, "retrieved_k": 0, "action_success": false }
}
```

**POST /requests/{request_key}/messages** *(folytatás / interaktív kitöltés)*
- input:
```json
{
  "role": "enduser",
  "text": "Hibakód: 0x0000011b",
  "meta": { "attachments": ["..."] }
}
```
- output: ugyanaz a schema, frissített kérdéslista vagy action.

**POST /ask** *(self-service)*
- **Stateless:** nem hoz létre `request` rekordot, nem ír DB-be (max. app log/metrics).
- **No workflow:** `workflow=null` és **nem** dispatch-ol action-t (ticket/email/approval).

- input:
```json
{ "role": "enduser", "question": "Hogyan kérek szabadságot?", "domain_hint": "hr" }
```
- output:
```json
{
  "request_key": null,
  "domain": "hr",
  "sub_route": null,
  "status": "DONE",
  "resolution": "SELF_SERVICE_OK",
  "questions": [],
  "answer": "… [CIT-1]",
  "citations": [
    { "cit_id": "CIT-1", "doc_id": "HR-POL-001", "chunk_id": "HR-POL-001#03", "score": 0.78, "source": "kb_hr" }
  ],
  "workflow": null,
  "metrics": { "latency_ms": 900, "retrieved_k": 5, "action_success": false }
}
```

**POST /updates**
- input:
```json
{
  "request_key": "KR-20251220-8F3K2D",
  "actor": "it_l2",
  "status": "DONE",
  "comment": "Account + groups done.",
  "event_id": "8b55a8b7-5d0a-4cde-b8a5-0c4c7f0b2d5a"
}
```
- output: request/task friss állapot.

**Integritás (ajánlott, demo-ban kapcsolható):**
- Header-ek:
  - `X-KR-Timestamp`: unix epoch (sec)
  - `X-KR-Signature`: `sha256=<hex>`
- Számítás: `sig = HMAC_SHA256(secret, f"{timestamp}.{raw_body}")`
- Ellenőrzés:
  - timestamp drift max ±300s,
  - konstans idejű signature compare,
  - `event_id` idempotencia (duplikált update → no-op + 200 OK).
- Demo kapcsoló: `UPDATES_VERIFY_SIGNATURE=false` esetén a signature check kihagyható, **de** az `event_id` idempotencia marad.


**GET /requests/{request_key}**
- státusz + taskok + timeline (events) + (opcionális) messages.

### 9.2 Action Sink Service (demo integration backend)

**Cél:** demózható “külső integráció”, ami valós HTTP POST-ot fogad és visszaad egy `external_id`-t.

#### Idempotencia (kötelező)
- Action Sink tárolja az `action_key`-t és **unique** legyen rá.
- Ha ugyanazzal az `action_key`-val érkezik újra a request:
  - **nem** hoz létre új rekordot,
  - a korábbi rekord `external_id`-ját adja vissza.

**POST /actions/{channel}**
- channel: `ticket|email|approval|procurement|webhook`
- body: tetszőleges JSON + ajánlott mezők:
  - `action_key` *(string, kötelező)*
  - `request_key` *(string)*
  - `action_type` *(string)*
  - `payload` *(object)*
- response: `{ "external_id":"AS-...", "received_at":"..." }`

**GET /actions/{channel}**
- lista (id, ts, payload summary).

**GET /actions/{channel}/{external_id}**
- részletek (teljes payload).

**DELETE /actions** *(opcionális)*
- demo reset.

---

## 10) LLM és RAG baseline

### 10.1 LLM (backend-only)
- KR Orchestrator hívja (kulcs: `OPENAI_API_KEY` env var).
- Használat:
  - intent/domain routing (ha kell),
  - question generation (quality gate),
  - RAG answer synthesis (citációs szabállyal).
- Kulcsok soha nem kerülnek frontendbe / repo-ba.

### 10.2 RAG pipeline

#### 10.2.1 Ingest (demo-szintű, de valódi)
Pipeline: dokumentum → chunk → embedding → upsert Qdrantba domain collectionbe.

**Kötelező ingest script (MVP):** `scripts/ingest_kb.py`
- Input: `--kb_dir ./kb` + Qdrant elérés + embedding kulcs/model envből.
- Viselkedés:
  - végigmegy a `kb/<domain>/` mappákon,
  - `doc_id` = fájlnév eleje az első `_` előtt (pl. `HR-POL-001`),
  - `title` = első H1 (fallback: fájlnév),
  - chunkol (600 token / 80 overlap),
  - upsert Qdrantba a domain collectionbe (`kb_hr`, `kb_it`, ...),
  - payload: `domain, doc_id, title, source, chunk_id, acl_roles[]`.
- Determinisztikus `chunk_id`: `{doc_id}#{idx:03d}` (így a citációk stabilak).


**Forrás struktúra (minimum):**
```
kb_sources/
  hr/
    HR-POL-001_vacation.md
    HR-SOP-010_onboarding.md
  compliance/
    COMP-POL-001_access_request.md
    COMP-POL-002_audit_logging.md
  it/
    IT-RUN-001_printer.md
    IT-RUN-002_vpn.md
    IT-RUN-003_password_reset.md
  ops/
    OPS-SOP-001_procurement.md
  general/
    GEN-TRIAGE-001_how_to_write_a_good_ticket.md
```

**Chunking defaultok (MVP):**
- ~600 token / chunk, ~80 token overlap
- `chunk_id = "{doc_id}#{idx:03d}"`

**Qdrant payload minimum:**
- `domain`, `doc_id`, `title`, `source` *(file path / wiki link)*, `chunk_id`
- `acl_roles[]` *(pl. ["hr"])*

#### 10.2.2 Retrieval
- `domain_router` dönt → csak a megfelelő domain collectionből keres.
- **Paraméterek (MVP default):**
  - `top_k = 6`
  - `min_score = 0.25` *(csak induló érték — a score skála függ a distance metrikától / embeddertől)*
- **Kalibráció (kötelező implementációs csiszolás):**
  - futtass egy 10–20 kérdéses mini tesztet, logold a top score eloszlást, és **env-ből állítható** threshold legyen (`KR_RETRIEVAL_MIN_SCORE`).
- **Metrikák:**
  - `metrics.retrieval_scores_top[]` = top-N score lista (pl. 6 elem)
  - `metrics.retrieval_score_max/avg` (opcionális, ha nem akarsz listát)
- ACL filter: csak olyan chunk jöhet vissza, ahol `role ∈ acl_roles` (vagy `acl_roles` üres = public).
- **Döntési szabály:**
  - `retrieved_k` = az **ACL + min_score** után megmaradó chunkok száma.
  - ha `retrieved_k == 0` → `resolution=NO_KB_HIT`, `citations=[]`, rövid sablon válasz.

#### 10.2.3 Answer synthesis
- Csak retrieved chunkokból.
- Ha kevés/0 találat: kötelező “nincs elég adat” sablon (NO_KB_HIT).

---

### 10.3 Citáció szabály (kötelező)

**Cél:** zero-hallucination demó, auditálható források.

**Bekezdés definíció (validatorhoz):**
- “Bekezdés” = nem üres szövegblokk, amit legalább egy üres sor (`\n\n`) választ el a következőtől.
- Lista/blokk (`- item`) egy bekezdésnek számít, ha nincs közte üres sor.

- Válasz szövegben: `[CIT-1] [CIT-2]` jelölések.
- `citations[]` objektumok kötelezően tartalmazzák a mappinget:
  - `cit_id` (CIT-1)
  - `doc_id`
  - `chunk_id`
  - `score`
  - `source` (pl. `kb_it`)
- `cit_id` csak olyan chunkra mutathat, ami a **retrieved** listában benne volt.
- Ha `retrieved_k == 0`:
  - `citations=[]`
  - `answer` = rövid “nincs elég adat” sablon
  - `resolution=NO_KB_HIT`

**Bekeztés-szintű kényszer:**
- Ha van retrieval (`retrieved_k > 0`), a válasz **minden bekezdésében** (lásd definíció fent) legyen legalább 1 citáció.
  - (Ezt a `validate_output` node ellenőrzi.)
- **Ha validáció fail:** írjon `events` rekordot `validation_failed` típussal + `validation_fail_reason`.
- **1 retry:** ugyanazzal a kontextussal, de “fixáld a citációkat/schema-t” utasítással.
- **Retry után is fail:** safe fallback kimenet:
  - ha quality gate szerint hiányos adat → `resolution=NEEDS_INFO`
  - különben → `resolution=NO_KB_HIT`
  - `answer` rövid sablon, `citations=[]`
  - `metrics.validation_fallback=true` + `events: validation_fallback`


---

## 11) LangGraph baseline (flow)

### 11.1 Állapot (State) minimál
- `request_key?`, `channel`, `role`, `text`, `meta`
- `domain`, `sub_route`, `intent`
- `required_fields`, `missing_fields`, `questions`, `answers_so_far`
- `retrieved_chunks[]`, `answer`, `citations[]`
- `workflow_action`, `external_id`
- `metrics`

### 11.2 Node-ok (MVP)
1) `parse_intake`
2) `enrich_public_api` *(opcionális)*
3) `route_domain` (+ IT sub-route, fallback general)
4) `quality_gate` (NEEDS_INFO vagy tovább)
5) `policy_check` (RBAC/ACL + guardrails)
6) `retrieve_kb` (domain collection)
7) `compose_response` (citációkkal)
8) `decide_action` (kell-e ticket/approval/procurement?)
9) `execute_action` (Action Sink POST)
10) `validate_output` (schema + citáció szabály)
11) `persist_audit` (DB event)
12) END

**Scheduler (külön fut):** `sla_tick` → reminder/escalation action.

---

## 12) Security / compliance baseline
- **RBAC:** requestben `role`, domain ACL enforced (retrieval filter `acl_roles`).
- **PII redaction:** logban/telemetriában maszkolás (email, tel, név opcionálisan).
- **Prompt injection:** külső input nem írhatja felül a retrieval policy-t; system prompt tiltja.
- **Webhook/update integritás:** HMAC signature a `POST /updates`-hez (`X-KR-Timestamp` + `X-KR-Signature`, drift check + konstans idejű compare). Demo-ban env-vel kapcsolható, de az `event_id` idempotencia kötelező.
- **Trust boundary:** Action Sink demo-only; éles integrációk adapteren keresztül.

---

## 13) Logging / audit / metrics
- Minden jelentős lépés `events` táblába:
  - routed, needs_info, policy_denied, retrieved, action_dispatched, update_received, closed
- Metrikák minimum:
  - `latency_ms`
  - `retrieved_k`
  - `action_success` (bool)
  - (később) token usage

---

## 14) Demo terv (vizsgára)
**Demó 3 kötelező scenarió:**
1) **HR self-service**: “hogyan kérek szabadságot?” → RAG + citáció, ticket nélkül.
2) **IT incident**: “nem megy a nyomtató” → quality gate kérdések → ticket action a sinkbe.
3) **Compliance access**: “kérek hozzáférést X-hez” → approval action a sinkbe + audit.

**Plusz (ha belefér):**
4) SLA tick → reminder action megjelenik a sinkben.

---

## 15) Roadmap (házik szerint)
- **HF1:** Public API hívás (enrichment) + Action Sink POST (valós action) + formázott output + log
- **HF2:** embeddings + Qdrant, domain collectionök
- **HF3:** RAG + citációs output contract
- **HF4:** LangGraph end-to-end + SLA tick + demo script

---

## 16) “Szent Grál” szabály
- A baseline az igazság forrása.
- Minden módosítás: baseline update + rövid changelog (1–3 bullet).
- Kód csak olyat implementál, ami baseline-ben már szerepel.
