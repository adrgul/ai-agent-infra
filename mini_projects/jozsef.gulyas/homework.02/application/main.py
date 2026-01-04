import os
from application.openai_gateway import OpenAIGateway
from application.vector_store import VectorStore
from application.cli_interface import CliInterface
from dotenv import load_dotenv

def absoluteFilePaths(directory):
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))

def main():
    load_dotenv()

    print("Loading documents, please wait...\n")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")

    openai_gateway = OpenAIGateway(
        api_key=openai_api_key,
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        completion_model=os.getenv("COMPLETION_MODEL", "gpt-4o-mini")
    )

    root_dir = os.path.dirname(os.path.abspath(__file__))
    documents_dir = os.path.join(root_dir, os.pardir, "documents")
    files = absoluteFilePaths(documents_dir)
    vector_store = VectorStore(openai_gateway=openai_gateway)
    vector_store.init(files)

    interface = CliInterface(openai_gateway=openai_gateway, vector_store=vector_store)
    interface.run()

if __name__ == "__main__":
    main()
