# AI Internal Knowledge Router - Fejlesztési Terv

Ezt a projektet választottam kidolgozásra. A cél egy intelligens vállalati tudásirányító ágens létrehozása LangGraph segítségével.

## Tervezett mérföldkövek

1. **Router Logika:** Intent felismerés (HR vs IT vs Legal).
2. **RAG Implementáció:** Egy választott domain (pl. HR) tudásbázisának beépítése.
3. **Multi-Vector Store:** A logika kiterjesztése több témakörre.
4. **Workflow Automatizáció:** Mockolt API hívások (Jira, File creation).

## Tech Stack

- Python
- LangChain / LangGraph
- OpenAI API
- Vector DB (Pinecone vagy Chroma)

## Knowledge Router - Document Search Module

Ez a modul a "Knowledge Router" ágens projekt alapköve. Egy objektum-orientált dokumentumkezelő és kereső rendszert valósít meg, amely előkészíti a terepet a későbbi vektoros (RAG) kereséshez.

## Funkciók

- **Dokumentum betöltés:** JSON alapú tudásbázis kezelése.
- **Keresés:** Kulcsszó alapú keresés címben, tartalomban és címkékben.
- **Típusosság:** Python Type Hints és DataClasses használata a robusztus kódért.

## Telepítés

```bash
pip install pytest
