"""Local filesystem storage for original resume PDFs."""

from pathlib import Path
from uuid import UUID, uuid4

from ugra.config.settings import Settings


class ResumeFileStorage:
    def __init__(self, settings: Settings):
        self._root = Path(settings.resume_storage_path)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: UUID, filename: str, data: bytes) -> tuple[UUID, Path]:
        file_id = uuid4()
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "resume.pdf"
        user_dir = self._root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / f"{file_id}_{safe_name}"
        path.write_bytes(data)
        return file_id, path

    def read(self, path: Path) -> bytes:
        return path.read_bytes()
