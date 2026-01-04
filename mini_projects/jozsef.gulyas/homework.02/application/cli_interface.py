class CliInterface:
    def __init__(self, openai_gateway, vector_store):
        self.openai_gateway = openai_gateway
        self.vector_store = vector_store

    def run(self):
        print("Welcome to the CLI Interface!")
        while True:
            history = []
            query = input("Enter your query (or 'exit' to quit): ")
            if query.lower() == 'exit':
                break
            results = self.vector_store.search(query, top_k=2)
            response = self.openai_gateway.get_completion(query, results, history)
            history.append((query, response))
            print(f"\nAssistant: {response}\n")
        print("\nGoodbye!")