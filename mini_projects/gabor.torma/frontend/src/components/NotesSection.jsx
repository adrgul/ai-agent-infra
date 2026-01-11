import React from 'react';
import { CheckCircle } from 'lucide-react';

const NotesSection = ({ notes }) => {
    return (
        <section className="notes-section card">
            <div className="card-header">
                <CheckCircle className="icon" />
                <h3>Key Points & Decisions</h3>
            </div>
            <ul className="notes-list">
                {notes.map((note, index) => (
                    <li key={index} className="note-item">{note}</li>
                ))}
            </ul>
        </section>
    );
};

export default NotesSection;
