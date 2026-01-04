import json
import os
import requests
from dotenv import load_dotenv

URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"

def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY must be set")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }

    with open("prompts/system_prompt.md", "r") as f:
        system_prompt = f.read()

    print(f"\nWelcome to the {MODEL} chatbot! Type 'exit' to quit.\n")

    data = {
        "model": MODEL,
        "response_format": {"type": "json_object"},
        "messages": [{
            "role": "system",
            "content": system_prompt
        }],
    }

    next_question = "How can I help you today? "

    while True:
        message = input(next_question)
        if (message == "exit"):
            break

        data["messages"].append({"role": "user", "content": message})
        response = requests.post(URL, headers=headers, json=data)
        if response.status_code == 200:
            try:
                reply_content = response.json()["choices"][0]["message"]["content"]
                reply_json = json.loads(reply_content)
                answer = reply_json.get("answer", reply_content)
                follow_up = reply_json.get("followUpQuestion", "How can I help you today?")

                print(f"\nAssistant: {answer}\n")
                next_question = f"{follow_up} "
                data["messages"].append({"role": "assistant", "content": reply_content})
            except (json.JSONDecodeError, KeyError):
                print(f"\nAssistant: {reply_content}\n")
                next_question = "How can I help you today? "
                data["messages"].append({"role": "assistant", "content": reply_content})
        else:
            print(f"Error: {response.status_code}")
            break

    print("\n\nGoodbye!")

if __name__ == "__main__":
    main()
