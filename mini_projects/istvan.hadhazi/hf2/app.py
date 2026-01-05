#!/usr/bin/env python3
"""
AI Knowledge Router - RAG System
Main Application
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Színes konzol
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = BLUE = YELLOW = RED = CYAN = MAGENTA = ""
    class Style:
        RESET_ALL = BRIGHT = ""

# Local imports
from infrastructure.llm_client import OpenAIClient
from infrastructure.vector_store import QdrantVectorStore
from infrastructure.document_loader import MarkdownDocumentLoader
from services.rag_service import RAGService

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeRouterApp:
    """Fő alkalmazás osztály"""
    
    def __init__(self):
        """Inicializálás - Dependency Injection"""
        
        # .env betöltése
        load_dotenv()
        
        # Infrastructure layer
        logger.info("Infrastructure layer inicializálása...")
        self.llm_client = OpenAIClient()
        self.vector_store = QdrantVectorStore(self.llm_client)
        self.document_loader = MarkdownDocumentLoader()
        
        # Service layer
        logger.info("Service layer inicializálása...")
        self.rag_service = RAGService(
            vector_store=self.vector_store,
            llm_client=self.llm_client,
            document_loader=self.document_loader
        )
        
        logger.info("✓ Alkalmazás inicializálva")
    
    def load_documents(self):
        """Dokumentumok betöltése"""
        
        print(f"\n{Fore.CYAN}Dokumentumok betöltése...{Style.RESET_ALL}")
        
        # Domain konfigurációk
        base_path = Path("documents")
        domains = [
            {"domain": "it", "path": str(base_path / "it")},
            {"domain": "hr", "path": str(base_path / "hr")},
            {"domain": "finance", "path": str(base_path / "finance")},
        ]
        
        # Betöltés
        stats = self.rag_service.load_domain_documents(domains)
        
        # Statisztikák kiírása
        for domain in ["it", "hr", "finance"]:
            if domain in stats:
                files = stats[domain]["files"]
                chunks = stats[domain]["chunks"]
                print(f"{Fore.GREEN}✓ {domain.upper()}: {files} dokumentum ({chunks} chunk){Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Összesen: {stats['total_chunks']} chunk betöltve{Style.RESET_ALL}\n")
    
    def print_header(self):
        """Fejléc"""
        print("\n" + "=" * 44)
        print(f"{Fore.CYAN}{Style.BRIGHT} AI Knowledge Router - RAG System{Style.RESET_ALL}")
        print("=" * 44)
    
    def print_answer(self, answer):
        """Válasz formázott kiírása"""
        
        # Releváns dokumentumok
        if answer.sources:
            print(f"\n{Fore.MAGENTA}🔍 Releváns dokumentumok:{Style.RESET_ALL}")
            for i, result in enumerate(answer.sources[:3], 1):
                chunk = result.chunk
                score = result.score
                print(f"  [{i}] {Fore.CYAN}{chunk.domain}/{chunk.source}{Style.RESET_ALL} ({score:.2f})")
        
        # Válasz
        print(f"\n{Fore.BLUE}📄 Válasz:{Style.RESET_ALL}")
        print(answer.answer)
        
        # Forrás
        if answer.sources:
            sources = set(f"{s.chunk.domain}/{s.chunk.source}" for s in answer.sources[:3])
            print(f"\n{Fore.YELLOW}[Források: {', '.join(sources)}]{Style.RESET_ALL}")
        
        print("\n" + "-" * 44)
    
    def run(self):
        """Fő loop"""
        
        self.print_header()
        
        # Dokumentumok betöltése
        try:
            self.load_documents()
        except Exception as e:
            print(f"{Fore.RED}Hiba a dokumentumok betöltésekor: {e}{Style.RESET_ALL}")
            logger.exception("Document loading error")
            return
        
        # Interaktív loop
        print(f"{Fore.GREEN}Kérdezz bármit!{Style.RESET_ALL} ('{Fore.YELLOW}exit{Style.RESET_ALL}' - kilépés)")
        print("-" * 44 + "\n")
        
        while True:
            try:
                # Input
                question = input(f"{Fore.GREEN}Kérdés: {Style.RESET_ALL}").strip()
                
                # Kilépés
                if question.lower() in ["exit", "quit", "bye"]:
                    print(f"\n{Fore.CYAN}Viszlát!{Style.RESET_ALL}\n")
                    break
                
                # Üres input
                if not question:
                    continue
                
                # Kérdés feldolgozása
                print(f"\n{Fore.CYAN}Keresés...{Style.RESET_ALL}")
                answer = self.rag_service.ask_question(question)
                
                # Válasz kiírása
                self.print_answer(answer)
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}Kilépés...{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"{Fore.RED}Hiba: {e}{Style.RESET_ALL}")
                logger.exception("Error processing question")


def main():
    """Main entry point"""
    
    try:
        app = KnowledgeRouterApp()
        app.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.CYAN}Kilépés...{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}Kritikus hiba: {e}{Style.RESET_ALL}")
        logger.exception("Critical error")
        sys.exit(1)


if __name__ == "__main__":
    main()

