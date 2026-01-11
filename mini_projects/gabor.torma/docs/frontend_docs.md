# MeetingAI Frontend Documentation

## Overview

The MeetingAI Frontend is a modern, responsive single-page application (SPA) built to interact seamlessly with the MeetingAI backend. It provides an intuitive interface for users to upload meeting transcripts and view the AI-generated insights, including summaries, tasks, and notes.

## Technology Stack

- **Core Framework**: React 19
- **Build Tool**: Vite 5
- **Language**: JavaScript (ES Modules)
- **Styling**: Vanilla CSS / Standard Vite styles
- **Icons**: Lucide React
- **Markdown Rendering**: React Markdown
- **Linting**: ESLint + React Plugins

## Application Structure

The project follows a standard Vite + React structure:

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── App.jsx          # Main application component
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML entry point
└── package.json         # Dependencies and scripts
```

## Features

1.  **File Upload Interface**:
    - Drag-and-drop or click-to-select functionality for `.txt` transcript files.
    - specialized validation to ensure correct file types.

2.  **Real-time Status**:
    - Visual feedback during the processing phase (loading states).

3.  **Result Visualization**:
    - **Executive Summary**: Rendered via Markdown for clean, readable formatting.
    - **Task Board**: Displays actionable items with assignees and priorities.
    - **Key Notes**: Lists extracted decisions and key points clearly.

## Setup & Development

### Prerequisites
- Node.js (v18 or higher recommended)
- npm (Node Package Manager)

### Local Installation

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The application will typically be available at `http://localhost:5173`.

### Configuration

The frontend is configured to communicate with the backend. Ensure the backend is running (default: `http://localhost:8000`) before testing the upload functionality.

- **Vite Config**: Defined in `vite.config.js`.
- **Linting**: Rules are defined in `eslint.config.js` to ensure code quality (React Hooks rules, etc.).

## Docker Usage

The frontend includes a `Dockerfile` for containerization. In the standard `docker-compose` setup:

- **Host**: Mapped to port `3000` (or as defined in `docker-compose.yml`).
- **Hot Reloading**: Configured to support changes during development in the container environment.

To run only the frontend via Docker:
```bash
docker-compose up --build frontend
```
