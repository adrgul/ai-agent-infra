import requests

class OpenAIGateway:
    EMBEDDING_URL = "https://api.openai.com/v1/embeddings"
    COMPLETION_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, completion_model: str, embedding_model: str):
        self.api_key = api_key
        self.completion_model = completion_model
        self.model = embedding_model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def get_completion(self, prompt, context, history):
        messages = [{
            "role": "user",
            "content": "You are a helpful assistant. Answer questions based on the provided context. Context is in json format, and it contains 'texts' field with relevant information. It also contains 'sources' with the source of the information. Include that in your answer as citation."
        }, {
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {prompt}"
        }]

        if history:
            for q, a in history:
                messages.insert({
                    "role": "user",
                    "content": q
                })
                messages.insert({
                    "role": "assistant",
                    "content": a
                })

        response = requests.post(
            self.COMPLETION_URL,
            headers=self.headers,
            json={
                "model": self.completion_model,
                "messages": messages
            }
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(f"Failed to get completion: {response.text}")
        return response.json()["choices"][0]["message"]["content"].strip()

    def get_embedding(self, text):
        response = requests.post(
            self.EMBEDDING_URL,
            headers=self.headers,
            json={
                "input": text,
                "model": self.model
            }
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(f"Failed to get embedding: {response.text}")
        return response.json()["data"][0]["embedding"]
