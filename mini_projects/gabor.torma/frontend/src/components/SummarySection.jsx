import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText } from 'lucide-react';

const SummarySection = ({ summary }) => {
    return (
        <section className="summary-section card">
            <div className="card-header">
                <FileText className="icon" />
                <h3>Executive Summary</h3>
            </div>
            <div className="markdown-body">
                <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
        </section>
    );
};

export default SummarySection;
