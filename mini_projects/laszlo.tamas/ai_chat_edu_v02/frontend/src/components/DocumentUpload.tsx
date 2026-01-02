/**
 * Document Upload Component
 * Allows users to upload PDF, TXT, or MD files for RAG processing
 */

import { useState } from "react";
import "./DocumentUpload.css";

const API_BASE_URL = import.meta.env.VITE_API_URL;

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = [".pdf", ".txt", ".md"];

interface DocumentUploadProps {
  tenantId: number;
  userId: number;
  compact?: boolean;
  isOpen?: boolean;
  onClose?: () => void;
}

export function DocumentUpload({ 
  tenantId, 
  userId, 
  compact = false,
  isOpen = false,
  onClose 
}: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [visibility, setVisibility] = useState<"private" | "tenant">("private");
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [progress, setProgress] = useState<string[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    setError(null);
    setSuccess(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    // Validate file type
    const fileExt = `.${selectedFile.name.split(".").pop()?.toLowerCase()}`;
    if (!ALLOWED_TYPES.includes(fileExt)) {
      setError(`Invalid file type. Allowed: ${ALLOWED_TYPES.join(", ")}`);
      setFile(null);
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File too large. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);
    setProgress([]);

    try {
      // Step 1: Upload started
      setProgress(prev => [...prev, "📤 Upload started..."]);
      
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tenant_id", tenantId.toString());
      formData.append("user_id", userId.toString());
      formData.append("visibility", visibility);

      setProgress(prev => [...prev, "📄 Document uploaded"]);

      // Use new workflow endpoint (automated pipeline)
      const response = await fetch(`${API_BASE_URL}/workflows/process-document`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Check if workflow succeeded or failed
      if (data.status === "failed") {
        // Show only completed steps from backend
        const summary = data.summary || {};
        const completedSteps = summary.completed_steps || [];
        
        if (completedSteps.includes("extraction")) {
          setProgress(prev => [...prev, "✂️ Content extracted"]);
        }
        if (completedSteps.includes("storage")) {
          setProgress(prev => [...prev, "💾 Stored in database"]);
        }
        if (completedSteps.includes("chunking")) {
          setProgress(prev => [...prev, "✂️ Document chunked"]);
        }
        if (completedSteps.includes("embedding")) {
          setProgress(prev => [...prev, "🔢 Embeddings generated"]);
        }
        
        // Show error
        const errorMsg = data.error || summary.error || "Processing failed";
        setError(errorMsg);
        setProgress(prev => [...prev, `❌ Error: ${errorMsg}`]);
        return;
      }
      
      // Success path: show all steps
      setProgress(prev => [...prev, "✂️ Document chunked"]);
      setProgress(prev => [...prev, "💾 Stored in database"]);
      setProgress(prev => [...prev, "🔢 Embeddings generated"]);
      setProgress(prev => [...prev, "🗄️ Stored in vector database"]);
      
      // Display success with workflow summary
      const summary = data.summary || {};
      setSuccess(
        `✅ Document "${summary.filename || file.name}" processed successfully!\n` +
        `📄 Document ID: ${data.document_id}\n` +
        `📊 Content: ${summary.content_length || 0} characters\n` +
        `🧩 Chunks: ${summary.chunk_count || 0}\n` +
        `🔢 Embeddings: ${summary.embedding_count || 0}\n` +
        `💾 Qdrant vectors: ${summary.qdrant_vectors || 0}`
      );
      
      setProgress(prev => [...prev, "✅ Processing complete!"]);
      
      // Reset form
      setFile(null);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Upload failed";
      setError(errorMsg);
      setProgress(prev => [...prev, `❌ Error: ${errorMsg}`]);
    } finally {
      setIsUploading(false);
    }
  };

  // Compact mode: render as modal
  if (compact) {
    if (!isOpen) return null;
    
    return (
      <div className="document-upload-modal-overlay" onClick={onClose}>
        <div className="document-upload-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>📎 Upload Document</h3>
            <button className="close-button" onClick={onClose}>
              ✕
            </button>
          </div>
          <div className="upload-form">
            <div className="form-group">
              <label htmlFor="file-input">Select File (PDF, TXT, MD):</label>
              <input
                id="file-input"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                disabled={isUploading}
              />
              {file && (
                <div className="file-info">
                  Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>

            <div className="form-group">
              <label>Visibility:</label>
              <div className="radio-group">
                <label>
                  <input
                    type="radio"
                    value="private"
                    checked={visibility === "private"}
                    onChange={(e) => setVisibility(e.target.value as "private")}
                    disabled={isUploading}
                  />
                  Private (me only)
                </label>
                <label>
                  <input
                    type="radio"
                    value="tenant"
                    checked={visibility === "tenant"}
                    onChange={(e) => setVisibility(e.target.value as "tenant")}
                    disabled={isUploading}
                  />
                  Tenant (all users)
                </label>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="upload-button"
            >
              {isUploading ? "Uploading..." : "Upload Document"}
            </button>

            {progress.length > 0 && (
              <div className="progress-log">
                {progress.map((step, index) => (
                  <div key={index} className="progress-step">
                    {step}
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div className="message error">
                ❌ {error}
              </div>
            )}

            {success && (
              <div className="message success">
                {success}
              </div>
            )}

            <div className="upload-info">
              <p><strong>Note:</strong> Documents will be chunked and embedded for RAG retrieval.</p>
              <p>Maximum file size: 10MB</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Original expanded mode for non-compact usage
  return (
    <div className="document-upload">
      <div className="document-upload-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>📄 Document Upload</h3>
        <button className="toggle-button">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="upload-form">
          <div className="form-group">
            <label htmlFor="file-input">Select File (PDF, TXT, MD):</label>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            {file && (
              <div className="file-info">
                Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Visibility:</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  value="private"
                  checked={visibility === "private"}
                  onChange={(e) => setVisibility(e.target.value as "private")}
                  disabled={isUploading}
                />
                Private (me only)
              </label>
              <label>
                <input
                  type="radio"
                  value="tenant"
                  checked={visibility === "tenant"}
                  onChange={(e) => setVisibility(e.target.value as "tenant")}
                  disabled={isUploading}
                />
                Tenant (all users)
              </label>
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="upload-button"
          >
            {isUploading ? "Uploading..." : "Upload Document"}
          </button>

          {progress.length > 0 && (
            <div className="progress-log">
              {progress.map((step, index) => (
                <div key={index} className="progress-step">
                  {step}
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="message error">
              ❌ {error}
            </div>
          )}

          {success && (
            <div className="message success">
              {success}
            </div>
          )}

          <div className="upload-info">
            <p><strong>Note:</strong> Documents will be chunked and embedded for RAG retrieval.</p>
            <p>Maximum file size: 10MB</p>
          </div>
        </div>
      )}
    </div>
  );
}
