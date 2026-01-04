# RAG + vektoradatbázis mintaszöveg (demó dokumentum)

> Cél: Ez a dokumentum kifejezetten RAG (Retrieval-Augmented Generation) és vektoradatbázis alapú agent működés demonstrálására készült.  
> A szöveg **jól chunkolható**: rövid, egyértelmű fejezetek, stabil alcímek, ismétlődő “mintázatok”, és több olyan bekezdés, amely önmagában is értelmezhető kontextust tartalmaz.  
> Nyelv: magyar, szakmai terminológiával.

---

## 1. Miért kell RAG egy agentnek?

A nagy nyelvi modellek erősek a szövegértésben és a generálásban, de alaphelyzetben nem “tudják”, hogy a szervezet belső szabályzataiban, specifikációiban vagy runbookjaiban mi az aktuális állapot. A RAG ezért nem pusztán egy kereső, hanem egy **kontrollált tudás-hozzáférési réteg**: a modell nem találgat, hanem forrásból dolgozik. A tipikus értéklánc egyszerűnek tűnik (keresés → válasz), de a minőség döntően azon múlik, hogyan alakítjuk ki a dokumentumfeldolgozást, a chunkolást, az embeddinget, a keresést és a kontextus összeállítását.

A RAG során a modell először “retrieval” lépést végez: releváns dokumentumrészleteket kér le egy indexből. A “generation” lépésben ezekre támaszkodva állít elő választ. A kulcs az, hogy a retrieval ne csak *valamit* adjon vissza, hanem **jó jelölteket** (high recall), majd a top találatok ténylegesen relevánsak legyenek (high precision). Ezt jellemzően több technika együtt adja: hibrid keresés, re-ranking, query rewriting és okos metadata-szűrés.

Egy agent környezetben a RAG különösen fontos, mert a döntési ciklus (Prompt → Decision → Tool → Observation → Memory) során a “Tool” hívás lehet egy kereső, és a “Memory” lehet egy tartós tudástár vagy beszélgetési állapot. A demóban tipikusan azt akarjuk megmutatni, hogy az agent **mikor** dönt úgy, hogy keres, **hogyan** fogalmazza át a kérdést a kereséshez, **mit** hoz vissza, és **hogyan** foglalja össze úgy, hogy a válasz hitelesen a forrásokra épüljön.

---

## 2. RAG referencia-architektúra röviden (end-to-end)

Egy tipikus RAG architektúra a következő rétegekből áll:

- **Ingestion / ETL**: források beolvasása (PDF, DOCX, HTML, jegykezelő, belső wiki, e-mail export).
- **Normalization**: tisztítás, kódolás egységesítése, fejléc/lábléc, oldalszámozás, duplikált sorok, tördelési hibák kezelése.
- **Chunking**: a dokumentum felosztása indexelhető egységekre.
- **Embedding**: minden chunkból vektor készül egy embedding modellel.
- **Index + Storage**: vektoradatbázis (ANN index), plusz nyers szöveg és metadata tárolása.
- **Retrieval**: vektoros, kulcsszavas (BM25) vagy hibrid keresés, metadata szűrők.
- **Re-ranking**: erősebb modell (cross-encoder vagy LLM) újrarendezi a jelölteket.
- **Context Packing**: a top-N chunkból “kontextuscsomag” épül, forráscímkékkel.
- **Generation**: az LLM válaszol, lehetőleg idézve a forrásokat.
- **Observability**: mérés (latency, token, recall@k, MRR), log és trace.
- **Governance**: hozzáférés-kezelés, adatvédelmi címkék, retention, audit.

A gyakorlatban a leggyakoribb félreértés, hogy “a vektoradatbázis majd megoldja”. Valójában az index csak a keresést gyorsítja; a minőséget a chunkolás, a query stratégia és a re-ranking adja. Ugyanazzal a vector DB-vel egy rosszul chunkolt tudásbázis gyenge lesz, míg egy jól chunkolt, jól felcímkézett korpusz nagyon magas minőséget ad.

---

## 3. Vektoradatbázis és embedding: mit tárolunk pontosan?

A vektoradatbázis a chunkok embedding vektorait tárolja. Egy rekord tipikusan tartalmaz:

- `id`: stabil azonosító (pl. dokumentum + szakasz + chunk sorszám).
- `text`: a chunk nyers szövege (vagy hivatkozás egy dokumentumtárra).
- `embedding`: a numerikus vektor (pl. 768/1024/1536 dimenzió).
- `metadata`: szűréshez és auditáláshoz szükséges mezők.

A hasonlósági keresés lényege, hogy a kérdés embeddingjét összehasonlítjuk a tárolt embeddingekkel. A hasonlósági mérték jellemzően cosine similarity vagy dot product. A vector DB gyorsításhoz ANN indexet használ (pl. HNSW, IVF), ami közelítő módszer, de nagy méretben nagyon gyors.

**Fontos demonstrációs pont**: a vektoros keresés szemantikát keres, nem kulcsszót. Ez jó, ha a felhasználó “más szavakkal” kérdez. Viszont a vektoros keresés néha “túl kreatív” is lehet: kapcsolódó fogalmakat hoz, de nem a konkrét, elvárt definíciót. Ezért erős minta a hibrid keresés és a re-ranking.

---

## 4. Chunkolás – a RAG minőség fő kapcsolója

A chunkolás célja, hogy a dokumentumot olyan egységekre bontsuk, amelyek:

1. elég kicsik ahhoz, hogy a retrieval pontos legyen és a prompt olcsó,
2. elég nagyok ahhoz, hogy a válaszhoz szükséges kontextus ne vesszen el,
3. szerkezetileg stabilak (címekhez, fejezetekhez köthetők),
4. jól címkézhetők metadata-val.

A “túl nagy chunk” tipikus tünete: a top találatban benne van a releváns mondat, de mellette sok irreleváns rész is. A generálás ezektől “elcsúszhat”, és a válasz túl hosszú, vagy félreértelmez. A “túl kicsi chunk” tipikus tünete: a modell visszakap egy definíciót, de hiányzik az előfeltétel, a kivétel vagy a példarész, így a válasz hiányos lesz.

**Gyakorlati baseline** (tokenben gondolkodva): 700–1200 token chunk és 10–20% overlap. Az overlap azért kell, mert a témák és mondatok nem igazodnak a vágási pontokhoz. Egy rövid átfedés biztosítja, hogy egy definíció és a közvetlen magyarázat ugyanabban a chunkban maradjon, vagy legalább a közelben legyen.

---

## 5. Chunkolási stratégiák (fix, szerkezeti, szemantikus, táblázat)

### 5.1 Fix méret + overlap
A legegyszerűbb stratégia: X tokenenként vágunk, és Y token overlap-et hagyunk. Ez stabil és gyors, de nem veszi figyelembe a dokumentum szerkezetét. Demóhoz jó, mert könnyű elmagyarázni a tradeoffokat.

### 5.2 Szerkezeti chunking
A dokumentum címsorai, alcímei, bekezdései alapján vágunk. Példa: minden `##` és `###` szint egy természetes határ. A módszer előnye, hogy a chunkok jobban “témásak”, és a metadata (pl. `section_path`) könnyen előáll.

### 5.3 Szemantikus chunking
A szöveg bekezdéseit embedeljük, majd a bekezdések közötti embedding-távolság alapján detektáljuk a témaváltást. Ha a távolság nagy, ott vágunk. Ez jobban kezeli az olyan dokumentumokat, ahol a formázás gyenge, de a témaváltás mégis erős.

### 5.4 Táblázatok chunkolása
A táblázatok különösen nehezek: a kontextus gyakran az oszlopnevekben van. Jó gyakorlat, hogy minden chunkba beírjuk az oszlopneveket, például:

- `Columns: Name | Owner | SLA | Escalation`
- `Row: Auth Service | Platform | 99.9% | on-call`

Ez chunkonként “önmagában is érthető” formát ad, és javítja a retrieval pontosságát.

---

## 6. Metadata – szűrés, hozzáférés, és magyarázhatóság

A metadata gyakran a RAG legnagyobb “rejtett” gyorsítója. Néhány minta mező:

- `source_id`, `doc_title`, `doc_type` (policy, spec, runbook, FAQ),
- `section_path` (pl. `3 / Chunking / Overlap`),
- `created_at`, `updated_at`, `version`,
- `owner_team` (platform, finance, ops),
- `language` (hu/en),
- `security_label` (public/internal/confidential),
- `tags` (pl. `rag`, `retrieval`, `embedding`, `rerank`).

A demóban jól mutat, ha ugyanarra a kérdésre kétféle retrievalt futtatunk:

1) szűrés nélkül: sok “kapcsolódó” találat, vegyes minőség,  
2) szűréssel: csak `doc_type=runbook` és `security_label=internal`, így célzott, releváns találatok.

Ez segít megértetni, hogy a RAG nemcsak szemantika, hanem **irányított keresés**.

---

## 7. Keresési stratégiák: vektoros, BM25, hibrid

### 7.1 Tisztán vektoros keresés
Előny: jól kezeli a szinonimákat, parafrázisokat, “másképp feltett” kérdéseket.  
Hátrány: néha olyan találatot hoz, ami “tematikusan közel van”, de a konkrét kulcsszót nem tartalmazza, így a válasz félrecsúszhat.

### 7.2 Tisztán kulcsszavas (BM25)
Előny: pontos, ha a kérdésben szerepelnek a dokumentum szó szerinti kifejezései.  
Hátrány: rosszabb, ha a felhasználó nem ismeri a belső terminológiát (pl. “token forgatás” helyett “kulcs csere”).

### 7.3 Hibrid keresés (ajánlott baseline)
A hibrid keresés a vektoros és kulcsszavas találatokat kombinálja. Gyakori stratégia: mindkét keresés ad jelölteket (pl. 50–50), majd összeolvasztjuk és re-rankeljük. A demóban ez különösen látványos: a hibrid találati lista általában stabilabb és megbízhatóbb.

---

## 8. Recall, precision és re-ranking (miért kell kétlépcsős retrieval?)

A retrieval első köre legyen “bő” és inkább recall-orientált: inkább hozzunk vissza 50 jelöltet, minthogy kihagyjunk egy kritikus definíciót. Ezután a re-ranking a precision-t növeli: kiválasztja a valóban releváns top-5-öt.

A re-ranking tipikusan egy erősebb, de drágább modell:

- **Cross-encoder**: kérdés + chunk együtt bemeneti pár, kimenet relevancia pontszám.
- **LLM-alapú rerank**: az LLM értékeli a jelölteket és rangsorol.

Demóban érdemes megmutatni, hogy vektoros top-1 néha nem a legjobb, de a top-20-ban ott van az igazi. A re-ranking képes ezt felhozni.

---

## 9. Query rewriting, multi-query, és “kérdésből keresőkérdés”

A felhasználói prompt gyakran nem keresésbarát. Például: “Miért kell overlap a chunkok között, és mekkora legyen?”  
Ebből a retrievalnek érdemes egy tömörebb, terminus-központú kérdést készíteni:

- “chunk overlap recommended size 10-20 percent”
- “overlap purpose boundary effects token windows”

A **query rewriting** célja, hogy a kérdésből “keresési kulcsokat” állítson elő. A **multi-query** pedig több variánst készít, például magyar/angol terminológiával, rövidítésekkel, és szinonimákkal. A demóban ezt úgy lehet láttatni, hogy ugyanarra a kérdésre futtatunk:

- alap query,
- átírt query,
- 3-5 multi-query variáns,

és megfigyeljük, mennyit javul a találati lista lefedettsége.

---

## 10. Kontextus összeállítás (context packing): “kevesebb, de jobb”

A generálás előtt a rendszer kontextust ad a modellnek. A tipikus hiba, hogy “tömködjük be” a top-10 chunkot. Ettől a prompt drága lesz, a modell elkalandozhat, és nő a kockázat, hogy irreleváns részeket is beemel a válaszba.

Jó gyakorlat, hogy:

- top-5 chunkot adunk,
- mindegyiket rövid, forráscímkézett blokként,
- ha hosszú, akkor célzottan kivágjuk a releváns részt (extract),
- a “policy” utasításban megmondjuk: csak a forrásokra támaszkodj, és ha nincs elég forrás, mondd ki.

**Minta forrásfejléc** (chunk elejére):
`[SOURCE: RAG_Demo_MD | Section: 4. Chunkolás | Chunk: 4-02 | Updated: 2025-12-31]`

---

## 11. Agent-ciklus demonstráció: Prompt → Decision → Tool → Observation → Memory

Az agent-ciklusban a felhasználó promptja után a modell dönt: kell-e tool hívás (pl. retrieval). A demóban jól elkülöníthető:

- **Decision**: “kell keresés”, mert definíciót és best practice-et kér, ami dokumentumban van.
- **Tool**: vector/hybrid search, metadata filter, top_k=20, majd rerank to top_k=5.
- **Observation**: a találatok és források összegzése, relevancia pontszámokkal.
- **Memory**: a végső válasz, plusz a “használt források” és a döntési indoklás röviden.

Kiemelten fontos: az agent memóriája nem ugyanaz, mint a tudásbázis. A tudásbázis tartós, verziózott, és auditálható. A beszélgetési memória rövid távú, és gyakran csak a felhasználó preferenciáit, döntéseit, vagy a feladat állapotát tartja.

---

## 12. Hozzáférés-kezelés és adatbiztonság (security boundary)

Valós vállalati RAG esetén a legnagyobb kockázat, hogy az agent “rossz” dokumentumokat is visszakeres. Ezért fontos:

- `security_label` szerinti szűrés,
- felhasználó jogosultságok metadata szinten,
- audit log: mit kért, mit talált, mit használt.

A demóban ezt úgy lehet bemutatni, hogy van ugyan egy “confidential” chunk, de a retrieval csak “internal” címkéig enged. Így a rendszer nemcsak okos, hanem kontrollált is.

---

## 13. Frissítés, verziózás, és index karbantartás

A RAG minősége idővel romolhat, ha:

- dokumentumok frissülnek, de az index nem,
- duplikált verziók maradnak bent,
- a “régi” chunkok magas hasonlóság miatt feljönnek.

Jó gyakorlat:

- `version` és `updated_at` metadata,
- deduplikáció (hash a normalizált szövegre),
- “soft delete” vagy “tombstone” jelölés,
- újraembedelés, ha embedding modellt váltunk.

Demóban érdemes egy bekezdést úgy írni, hogy “v2” és “v3” verzió is létezzen, és a retrievalt rávenni, hogy a frissebbet preferálja (szűrés vagy scoring boost).

---

## 14. Hibaminták és diagnosztika: hogyan derítsük ki, mi romlott el?

### 14.1 Retrieval nem találja a releváns részt
Okok:
- rossz chunkolás (a fogalom és a definíció külön chunkba került),
- rossz query (túl általános),
- nincs metadata szűrés (zaj),
- embedding modell nem illeszkedik a domainre.

### 14.2 Talál, de a modell rosszul válaszol
Okok:
- túl sok irreleváns chunk a kontextusban,
- nincs re-ranking,
- nincs utasítás a forrás-alapú válaszra,
- a chunk nem önmagában érthető (hiányzik az előzmény).

### 14.3 Hallucináció
Okok:
- a kontextus nem tartalmaz választ,
- a modell “kiegészíti” a hiányt,
- a rendszer nem engedi kimondani: “nincs elég forrás”.

A demóban nagyon jó, ha van egy kérdés, amire a dokumentum **nem** ad választ, és az agent helyesen azt mondja: “a rendelkezésre álló források alapján ez nem állapítható meg”.

