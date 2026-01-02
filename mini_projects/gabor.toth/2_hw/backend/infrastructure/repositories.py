"""Repository implementations for persistence."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

from domain.models import UserProfile, Message, Chunk, UploadedDocument, MessageRole
from domain.interfaces import (
    UserProfileRepository, SessionRepository, UploadRepository
)


class JSONUserProfileRepository(UserProfileRepository):
    """User profile repository using JSON files."""

    def __init__(self, data_dir: str = "data/users"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}.json"

    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from JSON."""
        path = self._get_profile_path(user_id)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return UserProfile(
            user_id=data["user_id"],
            language=data.get("language", "hu"),
            categories=data.get("categories", []),
            preferences=data.get("preferences", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    async def save_profile(self, profile: UserProfile) -> None:
        """Save user profile to JSON (atomic write)."""
        path = self._get_profile_path(profile.user_id)
        profile.updated_at = datetime.now()

        # Atomic write: temp file + rename
        temp_path = path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)

        temp_path.replace(path)


class JSONSessionRepository(SessionRepository):
    """Session repository using JSON files."""

    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        return self.data_dir / f"{session_id}.json"

    async def get_messages(self, session_id: str) -> List[Message]:
        """Load session messages from JSON."""
        path = self._get_session_path(session_id)
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        messages = []
        for item in data:
            messages.append(
                Message(
                    role=MessageRole(item["role"]),
                    content=item["content"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    metadata=item.get("metadata", {}),
                    user_id=item.get("user_id"),  # Load user_id from JSON
                )
            )
        return messages

    async def append_message(self, session_id: str, message: Message) -> None:
        """Append message to session (atomic write)."""
        messages = await self.get_messages(session_id)
        messages.append(message)

        path = self._get_session_path(session_id)
        temp_path = path.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(
                [m.to_dict() for m in messages],
                f, ensure_ascii=False, indent=2
            )

        temp_path.replace(path)

    async def clear_messages(self, session_id: str) -> None:
        """Clear all messages in session."""
        path = self._get_session_path(session_id)
        temp_path = path.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        temp_path.replace(path)


class FileUploadRepository(UploadRepository):
    """Upload repository using filesystem."""

    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.derived_dir = Path("data/derived")
        self.derived_dir.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        """Convert category name to slug for paths."""
        return text.lower().replace(" ", "_").replace("/", "_")

    def _get_category_dir(self, category: str) -> Path:
        """Get category directory: data/uploads/{category_slug}/"""
        category_slug = self._slugify(category)
        return self.base_dir / category_slug

    def _get_derived_dir(
        self, category: str, upload_id: str
    ) -> Path:
        """Get derived directory: data/derived/{category_slug}/{upload_id}/"""
        category_slug = self._slugify(category)
        return self.derived_dir / category_slug / upload_id

    def save_upload(
        self, category: str, upload_id: str,
        filename: str, content: bytes
    ) -> str:
        """Save uploaded file to category directory. Return file path."""
        upload_dir = self._get_category_dir(category)
        print(f"📁 Creating upload directory: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory exists: {upload_dir.exists()}")
        
        file_path = upload_dir / f"{upload_id}__{filename}"
        print(f"📝 Writing file to: {file_path}")
        try:
            file_path.write_bytes(content)
            print(f"✓ File saved successfully")
            print(f"✓ File exists: {file_path.exists()}")
            print(f"✓ File size: {file_path.stat().st_size} bytes")
        except Exception as e:
            print(f"❌ Error writing file: {e}")
            raise
        return str(file_path)

    def get_upload_path(
        self, category: str, upload_id: str, filename: str
    ) -> str:
        """Get path to saved upload."""
        upload_dir = self._get_category_dir(category)
        return str(upload_dir / f"{upload_id}__{filename}")

    def delete_upload(
        self, category: str, upload_id: str, filename: str
    ) -> None:
        """Delete uploaded file and derived artifacts."""
        # Delete upload file
        upload_path = self.get_upload_path(
            category, upload_id, filename
        )
        if os.path.exists(upload_path):
            os.remove(upload_path)

        # Delete derived folder
        derived_path = self._get_derived_dir(category, upload_id)
        if derived_path.exists():
            import shutil
            shutil.rmtree(derived_path)

    async def list_uploads(
        self, category: str
    ) -> List[UploadedDocument]:
        """List uploads for a category (shared across all users)."""
        upload_dir = self._get_category_dir(category)
        if not upload_dir.exists():
            return []

        uploads = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                # Parse filename: upload_id__original_filename
                parts = file_path.name.split("__", 1)
                if len(parts) != 2:
                    continue

                upload_id, filename = parts
                size = file_path.stat().st_size

                # Try to load metadata from derived chunks
                metadata = {}
                chunks = await self.load_chunks(category, upload_id)
                if chunks:
                    first_chunk = chunks[0]
                    metadata = {
                        "chunk_size_tokens": first_chunk.metadata.get("chunk_size_tokens", 900),
                        "overlap_tokens": first_chunk.metadata.get("overlap_tokens", 150),
                    }

                uploads.append(
                    UploadedDocument(
                        upload_id=upload_id,
                        user_id="shared",
                        filename=filename,
                        category=category,
                        size=size,
                        created_at=datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ),
                        metadata=metadata,
                    )
                )

        return uploads

    async def save_chunks(
        self, category: str, upload_id: str,
        chunks: List[Chunk]
    ) -> None:
        """Save chunks.json to derived artifacts folder."""
        derived_dir = self._get_derived_dir(category, upload_id)
        derived_dir.mkdir(parents=True, exist_ok=True)

        chunks_path = derived_dir / "chunks.json"
        temp_path = chunks_path.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(
                [chunk.to_dict() for chunk in chunks],
                f, ensure_ascii=False, indent=2
            )

        temp_path.replace(chunks_path)

    async def load_chunks(
        self, category: str, upload_id: str
    ) -> List[Chunk]:
        """Load chunks.json from derived artifacts folder."""
        derived_dir = self._get_derived_dir(category, upload_id)
        chunks_path = derived_dir / "chunks.json"

        if not chunks_path.exists():
            return []

        with open(chunks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = []
        for item in data:
            chunks.append(
                Chunk(
                    chunk_id=item["chunk_id"],
                    content=item["content"],
                    upload_id=item["upload_id"],
                    category=item["category"],
                    source_file=item["source_file"],
                    chunk_index=item["chunk_index"],
                    start_char=item["start_char"],
                    end_char=item["end_char"],
                    section_title=item.get("section_title"),
                    metadata=item.get("metadata", {}),
                )
            )

        return chunks
    async def save_description(
        self, category: str, description: str
    ) -> None:
        """Save category description to description.json in data/uploads/{category}/ folder."""
        category_dir = self._get_category_dir(category)
        category_dir.mkdir(parents=True, exist_ok=True)
        
        description_path = category_dir / "description.json"
        temp_path = description_path.with_suffix(".json.tmp")
        
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({"description": description}, f, ensure_ascii=False, indent=2)
        
        temp_path.replace(description_path)
        print(f"✓ Description saved: {description_path}")

    async def get_description(
        self, category: str
    ) -> Optional[str]:
        """Load category description from description.json in data/uploads/{category}/."""
        category_dir = self._get_category_dir(category)
        description_path = category_dir / "description.json"
        
        if not description_path.exists():
            return None
        
        try:
            with open(description_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("description")
        except Exception as e:
            print(f"❌ Error reading description: {e}")
            return None

    async def get_all_descriptions(self) -> dict:
        """Get all category descriptions from data/uploads/ directory."""
        descriptions = {}
        
        if not self.base_dir.exists():
            return descriptions
        
        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                description_path = category_dir / "description.json"
                if description_path.exists():
                    try:
                        with open(description_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        # Use slug as category name
                        descriptions[category_dir.name] = data.get("description")
                    except Exception as e:
                        print(f"❌ Error reading description from {category_dir}: {e}")
        
        return descriptions

    async def get_categories(self) -> List[str]:
        """Get list of all available categories (directories in uploads folder)."""
        if not self.base_dir.exists():
            return []
        
        categories = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                # Folder names are slugs (lowercase, underscores)
                categories.append(item.name)
        
        return sorted(categories)

    async def delete_category(self, category: str) -> None:
        """Delete entire category with all uploads and derived artifacts."""
        import shutil
        
        # Delete uploads directory for this category
        category_slug = self._slugify(category)
        uploads_dir = self.base_dir / category_slug
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
            print(f"✓ Deleted uploads directory: {uploads_dir}")
        
        # Delete derived files (chunks) for this category
        derived_category_dir = self.derived_dir / category_slug
        if derived_category_dir.exists():
            shutil.rmtree(derived_category_dir)
            print(f"✓ Deleted derived directory: {derived_category_dir}")
