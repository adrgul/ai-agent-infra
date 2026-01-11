# Feladat: Meglévő agent alkalmazás bővítése Hybrid RAG (ChromaDB) tudásbázissal + részletes debug UI + automatizált tesztek

## Kontextus
Egy már meglévő (Python) agent alkalmazásba kell beépítened egy vállalati jellegű tudásbázist (RAG), aminek elsődleges célja: **belső dokumentumokban (document/documents) keresés** és a válaszok ezekből való, forrásolt generálása.
A jelenlegi app valószínűleg tartalmaz chat UI-t, agent vezérlést (pl. LangGraph), és fallback mechanizmust (pl. web search). Ezt kell bővítened úgy, hogy **KB-first** működés legyen: először a belső dokumentumokból válaszoljon, és csak ha nincs releváns találat, akkor menjen tovább a fallback irányba.

## Kötelező technikai követelmények (NEM opcionális)
1) **Hybrid RAG** megvalósítás:
   - A retrieval legyen *hybrid*: 
     - (A) dense vector search (embedding) + 
     - (B) sparse/lexical keresés (BM25 vagy ekvivalens) +
     - (C) metadata filterek (pl. doc_type, source, created_at/version, access_scope)
   - A végső ranking legyen egyértelműen dokumentált (pl. weighted score vagy re-ranker), és legyen konfigurálható.

2) **ChromaDB** kötelező:
   - ChromaDB legyen a vector store (persistens módban).
   - Támogassa a dokumentumok incremental update-jét (új doksi hozzáadása, meglévő frissítése, törlés).

3) **Front-end debug nézet bővítése RAG információkkal (minél több annál jobb)**:
   A debug UI-ban minden kéréshez jeleníts meg részletes RAG telemetriát, minimum:
   - router döntés: KB-first -> ment-e RAG-re? (igen/nem, miért)
   - retrieval lekérdezés: query, normalizált query, filterek
   - top-k találatok táblázata: 
     - doc_id, doc_title/source, chunk_id, score_vector, score_sparse, score_final, rank
     - chunk preview (rövid excerpt) + “open full chunk” lehetőség
   - használt kontextus: a végül promptba küldött chunkok listája
   - citations: a válasz mely chunkokra hivatkozik
   - latency bontás: embed idő, chroma query idő, sparse query idő, merge/rerank idő, LLM time
   - token usage (ha elérhető)
   - fallback ok: ha fallback történt, miért (no_hit, low_confidence, policy)
   - konfiguráció snapshot: k, threshold, súlyok, retriever verzió
   - trace id / run id: hogy log/tracing és UI összeköthető legyen

4) **Minden legyen részletesen kommentálva a kódban**:
   - Nem “mit csinál” komment, hanem “miért így” kommentek.
   - Magyarázd el a tradeoffokat (chunking méret, overlap, scoring súlyok, threshold).

5) **SOLID elvek követése** (az alap app stílusához igazodva):
   - SRP: külön komponens legyen ingestion, chunking, embedding, vector retrieval, sparse retrieval, merge/rerank, answer synthesis, citations.
   - OCP: a retriever(ek) cserélhetők legyenek (interface/abstract base).
   - DIP: konfiguráció és külső függőségek (Chroma, embedder) injektálva legyenek.

6) **A fő cél: dokumentumokban keresés**:
   - Legyen világos “Document Search” pipeline.
   - A válasz kötelezően grounded legyen a visszahozott chunkokban; legyen forrásmegjelölés (doc + chunk).

7) **Automatizált, részletes tesztelés**:
   - Unit tesztek: chunker, sparse retriever, score merge, metadata filter, citations mapper.
   - Integration tesztek: ingestion -> index -> retrieval -> answer flow.
   - End-to-end tesztek: API/UI szinten (ha van ilyen réteg).
   - “Canary doc” teszt: tegyél be egy egyedi tokenes doksit, és bizonyítsd, hogy top-k-ban visszajön és a válasz hivatkozza.
   - “No-web” teszt: a web tool/mock le legyen tiltva; KB-ból válaszolható kérdés akkor is működjön.
   - Golden retrieval tesztek: legalább 20 kérdés + elvárt doc/chunk id (Recall@k / MRR jellegű assert).
   - Regressziós snapshot teszt: top-k doc/chunk listát rögzíts és hasonlíts (konfigurálható toleranciával).
   - CI-kompatibilis futtatás: gyors, determinisztikus, fix seed ahol kell.

## Implementációs irányelvek
### A) Tudásbázis adatmodell (javaslat)
- Document:
  - doc_id (stabil azonosító)
  - title
  - source (path/url)
  - doc_type
  - version / updated_at
  - access_scope (opcionális)
- Chunk:
  - chunk_id
  - doc_id
  - text
  - metadata (page, section, offsets)

### B) Chunking
- Legyen konfigurálható: chunk_size, chunk_overlap
- A chunking legyen tesztelt és determinisztikus.

### C) Hybrid retrieval részletek
- Dense retrieval: embedding + Chroma similarity search
- Sparse retrieval: BM25 (vagy egyenértékű; ha nincs lib, implementálható minimal, de preferált a bevált csomag)
- Merge:
  - normalizáld a score-okat (pl. min-max vagy z-score)
  - final_score = w_dense * dense_score + w_sparse * sparse_score (+ opcionális boost metadata alapján)
- Threshold:
  - legyen “no_hit” logika, ha a top1 final_score < threshold
  - ez hajtsa a routing fallback-et

### D) LangGraph / routing integráció
- A graphban legyen külön node:
  - `route_query`
  - `retrieve_kb_hybrid`
  - `synthesize_answer_with_citations`
  - `fallback_web_or_other_tools` (csak ha szükséges)
- A route döntést logold és mutasd a debug UI-ban.

### E) Observability
- Minden futásnál generálj `run_id`-t.
- Logold strukturáltan (JSON) a retrieval részleteket (top-k + score komponensek).
- A front-end debug panel ezeket az adatokat jelenítse meg.

## Repo változtatások – elvárt kimenet
- Új/átalakított modulok SOLID szerint (pl. `rag/` csomag):
  - `rag/ingestion/*`
  - `rag/chunking/*`
  - `rag/retrieval/dense.py` (Chroma)
  - `rag/retrieval/sparse.py` (BM25)
  - `rag/retrieval/hybrid.py` (merge + threshold)
  - `rag/citations.py`
  - `rag/config.py`
- Konfiguráció:
  - `.env` / config fájl: chroma persist dir, collection name, k, threshold, weights, chunk params
- Front-end:
  - Debug panel bővítése RAG adatokkal (táblázat, expandable chunk preview, latency breakdown).
- Tesztek:
  - `tests/unit/*`
  - `tests/integration/*`
  - `tests/e2e/*` (ha releváns)
  - Teszt fixture dokumentumok: `tests/fixtures/docs/*`

## Elfogadási kritériumok (Definition of Done)
1) A rendszer KB-first működik: belső doksikból válaszol, fallback csak no_hit/low_confidence esetén.
2) Hybrid retrieval ténylegesen működik és mérhető (dense + sparse score látszik a debugban).
3) ChromaDB persistens index létrejön és újraindítás után is használható.
4) A debug UI részletesen mutatja a RAG pipeline minden lépését és a top-k találatokat score bontással.
5) A válasz forrásolt (doc_id/chunk_id) és a citations megfeleltethetők a megjelenített kontextusnak.
6) Részletes, automatizált tesztek futnak zölden (unit + integration + canary + no-web + golden retrieval).
7) A kód tele van értelmes, “miért így” kommentekkel és SOLID elveket követ.

## Extra (opcionális, ha belefér)
- Admin endpoint vagy UI: “Reindex” / “Add document”
- Dokumentum duplikáció / version kezelés
- Simple RBAC metadata filter példa (legalább a struktúra legyen meg)

## Megjegyzés
Ne csak “hozzáadj” pár fájlt: integráld tisztán az architektúrába, a jelenlegi kódstílust követve.
Minden változtatásnál figyelj a determinisztikus tesztelhetőségre és a debug-olhatóságra.