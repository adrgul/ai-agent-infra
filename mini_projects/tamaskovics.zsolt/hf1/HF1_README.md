# HF1 – 2 db API hívás (public + OpenAI)

## Mit csinál?
- **Public API**: lekéri az aktuális időt (3rd-party “timestamp”) a WorldTimeAPI-ból.
- **OpenAI API**: ebből + a `--note` user inputból generál egy 1 soros “timestamp statement”-et.

## Telepítés
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Futtatás
### Csak public API (OpenAI nélkül)
```bash
cd mini_projects/tamaskovics.zsolt/hf1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env

python hf1_api_calls.py --note "Deploy elindítva"```

### Public + OpenAI
```bash
export OPENAI_API_KEY="YOUR_KEY"
python hf1_api_calls.py --timezone Europe/Budapest --note "Deploy elindítva" --model gpt-5-mini
```

## Kimenet
JSON, benne:
- `public_api.datetime`, `public_api.unixtime`
- `openai_api.output` (ha futott az OpenAI hívás)
