import React, { useState, useEffect } from 'react';
import { Search, Calendar, FileText, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './MeetingList.css';
import SummarySection from './SummarySection';
import NotesSection from './NotesSection';
import TasksSection from './TasksSection';

function MeetingList() {
    const [meetings, setMeetings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedMeeting, setSelectedMeeting] = useState(null);

    useEffect(() => {
        fetchMeetings();
    }, []);

    const fetchMeetings = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/meetings');
            if (response.ok) {
                const data = await response.json();
                setMeetings(data);
            }
        } catch (error) {
            console.error("Error fetching meetings:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) {
            fetchMeetings();
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(searchQuery)}`);
            if (response.ok) {
                const data = await response.json();
                setMeetings(data);
            }
        } catch (error) {
            console.error("Error searching meetings:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="meeting-list-container">
            <form onSubmit={handleSearch} className="search-bar">
                <input
                    type="text"
                    placeholder="Search meetings (e.g., 'database migration' or 'marketing strategy')..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                />
                <button type="submit" className="btn-search">
                    <Search size={18} /> Search
                </button>
            </form>

            {loading ? (
                <div className="loading">Loading...</div>
            ) : meetings.length === 0 ? (
                <div className="empty-state">No meetings found. Upload a transcript to get started!</div>
            ) : (
                <div className="meetings-grid">
                    {meetings.map((meeting) => (
                        <div
                            key={meeting.id}
                            className="meeting-card"
                            onClick={() => setSelectedMeeting(meeting)}
                        >
                            <div className="meeting-meta">
                                <span className="date">
                                    <Calendar size={14} style={{ marginRight: '4px' }} />
                                    {meeting.metadata?.date || 'Unknown Date'}
                                </span>
                                <span className="type">{meeting.metadata?.type || 'Meeting'}</span>
                            </div>
                            <div className="meeting-summary">
                                {meeting.metadata?.short_summary || meeting.metadata?.summary || (typeof meeting.content === 'string' ? meeting.content.slice(0, 150) + "..." : "No summary available.")}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {selectedMeeting && (
                <div className="meeting-detail-overlay" onClick={() => setSelectedMeeting(null)}>
                    <div className="meeting-detail-modal" onClick={e => e.stopPropagation()}>
                        <button className="close-btn" onClick={() => setSelectedMeeting(null)}>
                            <X size={20} />
                        </button>
                        <div className="modal-content">
                            <h2>Meeting Details</h2>
                            {selectedMeeting.metadata?.tasks ? (
                                <div className="results-grid">
                                    <SummarySection summary={selectedMeeting.metadata?.summary || selectedMeeting.content} />
                                    {selectedMeeting.metadata?.notes && (
                                        <NotesSection notes={selectedMeeting.metadata.notes} />
                                    )}
                                    {selectedMeeting.metadata?.tasks && (
                                        <TasksSection tasks={selectedMeeting.metadata.tasks} />
                                    )}
                                </div>
                            ) : (
                                <div className="markdown-body">
                                    <ReactMarkdown>
                                        {selectedMeeting.content || selectedMeeting.metadata?.summary || "Summary not available in list view."}
                                    </ReactMarkdown>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default MeetingList;
