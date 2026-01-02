# Encoding Debug Panel - Implementáció Dokumentáció

## Áttekintés

A felhasználó UTF-8 encoding problémát észlelt (magyar ékezetes betűk helytelenül jelenik meg: `Ã©` helyett `é`). 

A megoldáshoz létrehoztunk egy lépésről-lépésre működő debug panelt amely:
1. Reset-eli az adatbázisokat
2. Feltölt egy dokumentumot
3. Minden lépésnél megmutatja az első 200 karaktert encoding ellenőrzéshez

## Backend Implementáció

### 1. Debug Endpoint-ok
**Fájl:** [backend/api/debug_endpoints.py](backend/api/debug_endpoints.py)

#### POST /api/debug/reset/postgres
- Törli az összes dokumentumot és chunk-ot a PostgreSQL-ből
- Reset-eli a sequence-eket (id 1-től kezdődik újra)
- Response: `{ status, documents_deleted, chunks_deleted }`

#### POST /api/debug/reset/qdrant
- Törli az összes pontot a Qdrant r_d_ai_chat_document_chunks collection-ből
- Filter használatával (tenant_id alapján)
- Response: `{ status, points_deleted, collection }`

#### GET /api/debug/documents/{id}/preview
- Visszaadja a dokumentum első 200 karakterét
- Encoding ellenőrzéshez használható
- Response: `{ document_id, title, preview, full_length, source, visibility, tenant_id, user_id }`

#### GET /api/debug/documents/{id}/chunks/preview?limit=5
- Visszaadja a chunk-ok első 200 karakterét (limit darabot)
- Minden chunk-ot külön mutat
- Response: `{ document_id, chunks_count, chunks: [{ chunk_id, chunk_index, preview, full_length }] }`

### 2. Router Integráció
**Fájl:** [backend/api/routes.py](backend/api/routes.py)

```python
from api.debug_endpoints import router as debug_router
router.include_router(debug_router)
```

## Frontend Implementáció

### 1. Debug Panel Komponens
**Fájl:** [frontend/src/components/EncodingDebugPanel.tsx](frontend/src/components/EncodingDebugPanel.tsx)

**State Management:**
- `currentStep`: 0-5 (lépések követése)
- `documentId`: feltöltött dokumentum ID
- `uploadedFile`: kiválasztott fájl
- `documentPreview`: dokumentum első 200 karaktere
- `chunksPreview`: chunk-ok első 200 karaktere (array)
- `postgresPreview`: PostgreSQL-ből visszaolvasott első 200 karakter
- `isLoading`, `error`, `successMessage`: UI state

**Workflow Lépések:**

#### Step 0: Reset Databases
```typescript
handleReset()
  → POST /api/debug/reset/postgres
  → POST /api/debug/reset/qdrant
  → Success: currentStep = 1
```

#### Step 1: Upload Document
```typescript
handleUpload()
  → POST /api/documents/upload (FormData)
  → GET /api/debug/documents/{id}/preview
  → Show documentPreview
  → Success: currentStep = 2
```

#### Step 2: Chunk Document
```typescript
handleChunk()
  → POST /api/documents/{id}/chunk
  → GET /api/debug/documents/{id}/chunks/preview?limit=3
  → Show chunksPreview (first 3 chunks)
  → Success: currentStep = 3
```

#### Step 3: Verify PostgreSQL
```typescript
handleVerifyPostgres()
  → GET /api/debug/documents/{id}/chunks/preview?limit=3
  → Show postgresPreview (first chunk)
  → Success: currentStep = 4
```

#### Step 4: Embed to Qdrant
```typescript
handleEmbed()
  → POST /api/documents/{id}/embed
  → Success: currentStep = 5 (Complete!)
```

### 2. CSS Stílusok
**Fájl:** [frontend/src/styles/DebugPanel.css](frontend/src/styles/DebugPanel.css)

**Főbb elemek:**
- `.encoding-debug-panel` - Fő konténer (800px max-width, centrált)
- `.debug-step.active` - Aktív lépés (zöld border)
- `.debug-step.inactive` - Inaktív lépés (szürke, opacity 0.6)
- `.debug-preview` - Preview doboz (zöld border, pre tag a szöveghez)
- `.debug-error` - Hibaüzenet (piros háttér)
- `.debug-success` - Sikeres művelet (zöld háttér)
- `.debug-complete` - Teljes flow befejezve (gradient háttér)

### 3. App Integráció
**Fájl:** [frontend/src/App.tsx](frontend/src/App.tsx)

```tsx
import { EncodingDebugPanel } from "./components/EncodingDebugPanel";

<main className="app-main">
  <HowTo />
  
  {selectedUserId && selectedTenantId && (
    <>
      <EncodingDebugPanel 
        tenantId={selectedTenantId} 
        userId={selectedUserId} 
      />
      
      <DocumentUpload 
        tenantId={selectedTenantId} 
        userId={selectedUserId} 
      />
    </>
  )}
  
  <ChatWindow messages={messages} />
</main>
```

## Használati Útmutató

### 1. Frontend Elérés
```
http://localhost:3000
```

### 2. Lépések
1. **Tenant és User kiválasztása** a dropdown-okból
2. **Scroll le** az "Encoding Debug Panel"-hez
3. **Reset**: Kattints a "Reset PostgreSQL & Qdrant" gombra
4. **Fájl kiválasztása**: Válassz egy UTF-8 magyar dokumentumot (.txt, .md)
5. **Upload**: Kattints az "Upload" gombra
6. **Preview ellenőrzés**: Nézd meg az első 200 karaktert - helyesek az ékezetes betűk?
7. **Chunk**: Kattints a "Chunk" gombra
8. **Chunks Preview**: Ellenőrizd a chunk-ok első 200 karakterét
9. **Verify PostgreSQL**: Kattints a "Read from PostgreSQL" gombra
10. **PostgreSQL Preview**: Ellenőrizd hogy a visszaolvasott szöveg helyes-e
11. **Embed**: Kattints az "Embed to Qdrant" gombra
12. **Complete**: Siker esetén zöld "Process Complete!" üzenet jelenik meg

### 3. Encoding Ellenőrzés
**Minden preview-nál nézd meg:**
- Megjelennek-e helyesen az ékezetes betűk? (á, é, í, ó, ö, ő, ú, ü, ű)
- Nincs-e `Ã©` vagy `Ã¡` típusú hibás karakter?
- A szóközök és sortörések helyesek-e?

### 4. Problémák Megoldása

#### Ha hibás encoding jelenik meg:
1. **Dokumentum feltöltésnél**: Ellenőrizd hogy a fájl UTF-8 encoding-gal van-e mentve
2. **PostgreSQL-nél**: Ellenőrizd a `client_encoding: "UTF8"` beállítást [backend/database/pg_connection.py](backend/database/pg_connection.py#L27)-ben
3. **Backend response-nál**: Ellenőrizd a FastAPI `response_model` encoding-ját
4. **Frontend megjelenítésnél**: Ellenőrizd a `<meta charset="UTF-8">` tag-et

#### Ha a reset nem működik:
1. Nézd meg a backend logokat: `docker logs ai_chat_phase2-backend-1 --tail 50`
2. Ellenőrizd a PostgreSQL connection-t
3. Ellenőrizd a Qdrant API key-t (`.env` fájlban)

## PowerShell Teszt Scriptek

### 1. reset_databases.ps1
- PostgreSQL és Qdrant törlése
- Alternatív megoldás ha a frontend reset nem működik

### 2. test_debug_panel.ps1
- Backend endpoint elérhetőség teszt
- Használati útmutató kiírása

### 3. test_fantasy_full.ps1
- Teljes workflow teszt (upload → chunk → embed → RAG query)
- Használható a debug panel után is

## Technikai Részletek

### Backend Dependencies
- FastAPI
- psycopg2-binary (PostgreSQL)
- qdrant-client
- Meglévő services: DocumentService, QdrantService, ConfigService

### Frontend Dependencies
- React 18
- TypeScript
- Fetch API (built-in)

### Database
**PostgreSQL táblák:**
- `documents` (id, tenant_id, user_id, title, content, source, visibility, created_at)
- `document_chunks` (id, document_id, chunk_index, content, created_at)

**Qdrant collection:**
- `r_d_ai_chat_document_chunks` (vector: 3072 dimensions, payload: tenant_id, user_id, visibility, etc.)

### API Endpoints Összefoglalás

| Method | Endpoint | Cél |
|--------|----------|-----|
| POST | /api/debug/reset/postgres | PostgreSQL törlés |
| POST | /api/debug/reset/qdrant | Qdrant törlés |
| GET | /api/debug/documents/{id}/preview | Dokumentum preview |
| GET | /api/debug/documents/{id}/chunks/preview | Chunk-ok preview |
| POST | /api/documents/upload | Dokumentum feltöltés |
| POST | /api/documents/{id}/chunk | Dokumentum chunkolás |
| POST | /api/documents/{id}/embed | Embedding létrehozás |

## Következő Lépések

### Ha az encoding rendben van:
1. Tesztelj nagy fantasy dokumentummal (3000+ karakter)
2. Ellenőrizd a RAG query-t a chat-ben
3. Nézd meg hogy a források helyesen jelennek-e meg

### Ha az encoding hibás:
1. Ellenőrizd a PostgreSQL `client_encoding` beállítást
2. Tesztelj különböző fájl encoding-okkal (UTF-8, UTF-8 BOM, ISO-8859-2)
3. Nézd meg a backend log-okat minden lépésnél
4. Használd a `file` parancsot (Linux/Mac) vagy PowerShell-ben: `[System.IO.File]::ReadAllBytes()` hogy nézd meg a fájl encoding-ját

## Státusz

✅ **Backend debug endpoint-ok** - KÉSZ  
✅ **Frontend debug panel** - KÉSZ  
✅ **PostgreSQL reset** - KÉSZ  
✅ **Qdrant reset** - KÉSZ  
✅ **Lépésről-lépésre workflow** - KÉSZ  
✅ **Preview minden lépésnél** - KÉSZ  

🎯 **Ready for encoding troubleshooting!**
