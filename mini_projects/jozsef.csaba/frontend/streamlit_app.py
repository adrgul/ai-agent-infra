"""
Streamlit frontend for RAG chatbot.

Why this module exists:
- Provides user-friendly chat interface
- Connects to FastAPI backend via REST API
- Displays answers with source attributions

Design decisions:
- No conversation history sent to backend (stateless)
- Chat history maintained locally for UI display only
- Sidebar for backend URL config and ingestion controls
- Expandable sources section for each response
"""

import uuid
from typing import Any, Dict, List

import requests
import streamlit as st

# Page configuration
# Why wide layout: Better for chat UI with sidebar
st.set_page_config(
    page_title="RAG Chatbot Demo",
    page_icon="🤖",
    layout="wide",
)

# Constants
# Why session_id: Correlates requests/responses in UI (not used for memory)
SESSION_ID = str(uuid.uuid4())

# Sidebar configuration
# Why sidebar: Keeps controls separate from chat flow
st.sidebar.title("⚙️ Configuration")

# Backend URL input
# Why configurable: Allows switching between local and deployed backend
default_backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")
backend_url = st.sidebar.text_input(
    "Backend URL",
    value=default_backend_url,
    help="FastAPI backend URL (e.g., http://localhost:8000)"
)

# Retrieval parameters
# Why configurable: Allows experimenting with different RAG settings
st.sidebar.divider()
st.sidebar.subheader("RAG Parameters")

top_k = st.sidebar.slider(
    "Top K",
    min_value=1,
    max_value=10,
    value=4,
    help="Number of document chunks to retrieve"
)

temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.2,
    step=0.1,
    help="LLM temperature (0=deterministic, 1=creative)"
)

# Ingestion controls
# Why in sidebar: Separate from main chat flow but easily accessible
st.sidebar.divider()
st.sidebar.subheader("Document Ingestion")

if st.sidebar.button("🔄 Ingest Documents", use_container_width=True):
    """
    Call /ingest endpoint to build/rebuild vector store.

    Why force_rebuild=True: Button click implies user wants to rebuild,
    whether or not index already exists.
    """
    with st.sidebar:
        with st.spinner("Ingesting documents..."):
            try:
                response = requests.post(
                    f"{backend_url}/ingest",
                    json={"force_rebuild": True},
                    timeout=60,  # Ingestion can take time
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Ingestion complete!")

                    # Display ingestion statistics
                    # Why show details: Confirms what was indexed
                    st.write(f"**Indexed files:** {data['indexed_files']}")
                    st.write(f"**Total chunks:** {data['chunk_count']}")

                    # Display filenames
                    # Why expander: Keeps UI clean when many files
                    with st.expander("📄 Indexed files"):
                        for filename in data["filenames"]:
                            st.write(f"- {filename}")

                else:
                    st.error(f"❌ Ingestion failed: {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Is it running?")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Main chat interface
st.title("🤖 RAG Chatbot Demo")
st.caption("Ask questions about your indexed documents")

# Initialize chat history in session state
# Why session_state: Persists across reruns (Streamlit reruns on every interaction)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
# Why iterate: Show all previous messages in conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display sources if present (for assistant messages)
        # Why check: Only assistant messages have sources
        if "sources" in message:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**{i}. {source['filename']}** (`{source['source_id']}`)")
                    st.caption(source["snippet"])
                    st.divider()

# Chat input
# Why chat_input: Streamlit's dedicated chat input widget (better UX than text_input)
if prompt := st.chat_input("Ask a question about your documents..."):
    """
    Handle user message submission.

    Flow:
    1. Display user message
    2. Call /chat endpoint
    3. Display assistant response with sources
    4. Handle errors gracefully
    """

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        # Show spinner while waiting for response
        # Why spinner: Provides feedback during API call
        with st.spinner("Thinking..."):
            try:
                # Call /chat endpoint
                # Why POST: Sending message data
                response = requests.post(
                    f"{backend_url}/chat",
                    json={
                        "session_id": SESSION_ID,
                        "message": prompt,
                        "top_k": top_k,
                        "temperature": temperature,
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    # Success: Display answer and sources
                    data = response.json()
                    answer = data["answer"]
                    sources = data["sources"]

                    # Display answer
                    st.markdown(answer)

                    # Display sources in expander
                    # Why expander: Keeps chat clean, sources available on demand
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"**{i}. {source['filename']}** (`{source['source_id']}`)")
                            st.caption(source["snippet"])
                            st.divider()

                    # Add to chat history
                    # Why store sources: Needed for re-display on rerun
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })

                elif response.status_code == 409:
                    # Vector store not found: Direct user to ingest
                    # Why 409 handling: Common error when starting app
                    error_msg = "⚠️ Vector store not found. Please click 'Ingest Documents' in the sidebar first."
                    st.warning(error_msg)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })

                else:
                    # Other errors
                    error_msg = f"❌ Error {response.status_code}: {response.text}"
                    st.error(error_msg)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })

            except requests.exceptions.ConnectionError:
                # Backend not reachable
                # Why specific handling: Common during development
                error_msg = f"❌ Cannot connect to backend. Is it running at {backend_url}?"
                st.error(error_msg)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

            except requests.exceptions.Timeout:
                # Request timeout
                error_msg = "❌ Request timed out. Try again with fewer documents or smaller top_k."
                st.error(error_msg)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

            except Exception as e:
                # Unexpected errors
                error_msg = f"❌ Unexpected error: {e}"
                st.error(error_msg)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# Footer
# Why footer: Provides helpful links and context
st.sidebar.divider()
st.sidebar.caption("📖 [Documentation](https://github.com)")
st.sidebar.caption(f"💻 FastAPI Backend: {backend_url}")
st.sidebar.caption(f"🔑 Session ID: {SESSION_ID[:8]}...")
