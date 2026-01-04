import os
import json
from typing import List, Dict

class JSONHistorySearchTool:
    def __init__(self, base_dir="data/sessions"):
        self.base_dir = base_dir

    def search(self, query: str) -> List[Dict]:
        results = []
        for filename in os.listdir(self.base_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.base_dir, filename)
                with open(file_path, "r") as file:
                    session_data = json.load(file)
                    for message in session_data.get("messages", []):
                        if query.lower() in message.get("content", "").lower():
                            results.append({
                                "session_id": filename.replace(".json", ""),
                                "snippet": message["content"],
                                "timestamp": message["timestamp"]
                            })
        return results