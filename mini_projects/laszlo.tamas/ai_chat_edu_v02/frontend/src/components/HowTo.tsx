import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./HowTo.css";

export function HowTo() {
  const [content, setContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Load HOW_TO.md directly
    fetch("/api/howto/HOW_TO.md")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.text();
      })
      .then((text) => {
        setContent(text);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load HOW_TO.md:", err);
        setError("Nem sikerült betölteni a HOW_TO.md fájlt");
        setIsLoading(false);
      });
  }, []);

  if (error) {
    return (
      <div className="howto-panel">
        <div className="howto-content">
          <p className="howto-error">{error}</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="howto-panel">
        <div className="howto-content">
          <p className="howto-loading">Betöltés...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="howto-panel">
      <div className="howto-header">
        <h2>📖 Tesztelési Útmutató</h2>
      </div>
      <div className="howto-content">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}

