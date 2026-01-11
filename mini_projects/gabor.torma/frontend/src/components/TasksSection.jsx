import React from 'react';
import { Clock } from 'lucide-react';

const TasksSection = ({ tasks }) => {
    return (
        <section className="tasks-section card">
            <div className="card-header">
                <Clock className="icon" />
                <h3>Action Items</h3>
            </div>
            <div className="table-responsive">
                <table className="tasks-table">
                    <thead>
                        <tr>
                            <th>Task</th>
                            <th>Assignee</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tasks.map((task, index) => (
                            <tr key={index}>
                                <td>{task.title}</td>
                                <td><span className="badge">{task.assignee}</span></td>
                                <td>{task.due_date || "-"}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    );
};

export default TasksSection;
