# HF2 – Ops Notes (developer runbook)

## Qdrant ellenőrző parancsok

### Ready
```bash
curl -sS http://127.0.0.1:6333/readyz ; echo
```

### Collections list
```bash
curl -sS http://127.0.0.1:6333/collections | python3 -m json.tool
```

### Collection info
```bash
DOMAIN=it
curl -sS "http://127.0.0.1:6333/collections/$DOMAIN" | python3 -m json.tool
```

### Count
```bash
DOMAIN=it
curl -sS -X POST "http://127.0.0.1:6333/collections/$DOMAIN/points/count"   -H 'Content-Type: application/json'   -d '{"exact": true}' | python3 -m json.tool
```

## Router debug
A router minden domainben lefuttat top1 keresést, és a score-okból választ.

```bash
./.venv/bin/python scripts/router_search.py --query "Sev1 war-room" --min_score 0.0
```

Ha túl sok a fallback / rossz a választás:
- `.env`: `ROUTER_THRESHOLD` tuning

## Logok
```bash
docker logs qdrant | tail -n 200
```

## Data path
- host: `./qdrant_storage/`
- container: `/qdrant/storage`
