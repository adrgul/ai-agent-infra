import React from 'react';
import '../styles/citation-modal.css';

interface Citation {
  chunk_id: string;
  content: string;
  source_file: string;
  section_title: string;
  distance: number;
}

interface CitationModalProps {
  isOpen: boolean;
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ isOpen, citation, onClose }) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="citation-modal-overlay" onClick={onClose}>
      <div className="citation-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="citation-modal-header">
          <h3>Forrás információ</h3>
          <button className="citation-modal-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="citation-modal-body">
          <div className="citation-info">
            <div className="citation-field">
              <span className="citation-label">📄 Dokumentum:</span>
              <span className="citation-value">{citation.source_file}</span>
            </div>
            
            {citation.section_title && (
              <div className="citation-field">
                <span className="citation-label">📋 Szakasz:</span>
                <span className="citation-value">{citation.section_title}</span>
              </div>
            )}
            
            <div className="citation-field">
              <span className="citation-label">🔍 Relevancia:</span>
              <span className="citation-value">
                {(1 - citation.distance).toFixed(2)} / 1.0
              </span>
            </div>
            
            <div className="citation-field">
              <span className="citation-label">🆔 Chunk ID:</span>
              <span className="citation-value" style={{ fontSize: '0.9em' }}>
                {citation.chunk_id}
              </span>
            </div>
          </div>
          
          <div className="citation-content-section">
            <h4>Teljes szöveg:</h4>
            <div className="citation-content">
              {citation.content}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
