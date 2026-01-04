import { useEffect, useState } from "react";
import "./HowTo.css";

export function HowTo() {
  const [content, setContent] = useState<string>("");

  useEffect(() => {
    fetch("/HOW_TO.md")
      .then((res) => res.text())
      .then((text) => setContent(text))
      .catch((err) => console.error("Failed to load HOW_TO.md:", err));
  }, []);

  if (!content) return null;

  return (
    <div className="howto-panel">
      <div className="howto-content">
        <pre>{content}</pre>
      </div>
    </div>
  );
}
