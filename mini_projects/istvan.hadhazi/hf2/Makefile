.PHONY: help build run clean logs

help:
	@echo "AI Knowledge Router - RAG System"
	@echo ""
	@echo "Parancsok:"
	@echo "  make build   - Docker image build"
	@echo "  make run     - Alkalmazás indítása (interaktív)"
	@echo "  make clean   - Konténerek és volume-ok törlése"
	@echo "  make logs    - Qdrant logok megtekintése"
	@echo "  make local   - Lokális futtatás (Python)"
	@echo ""

build:
	@echo "Docker image build..."
	docker-compose build

run:
	@echo "Knowledge Router indítása..."
	@echo "Kilépés: 'exit' vagy Ctrl+D"
	@echo ""
	docker-compose up -d qdrant
	@sleep 3
	docker-compose run --rm app

clean:
	@echo "Cleanup..."
	docker-compose down -v
	docker rmi knowledge-router-app 2>/dev/null || true

logs:
	docker-compose logs -f qdrant

local:
	@echo "Lokális futtatás..."
	@echo "Ellenőrizd hogy a Qdrant fut-e: docker run -d -p 6333:6333 qdrant/qdrant"
	python app.py

