import hashlib

from modules.commission.constants import FILE_READ_CHUNK_SIZE


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(FILE_READ_CHUNK_SIZE), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def append_processing_note(existing_notes: str | None, note: str) -> str:
    """Append a note to processing_notes without clobbering existing entries."""
    cleaned_note = note.strip()
    if not cleaned_note:
        return existing_notes or ""

    if not existing_notes:
        return cleaned_note

    existing_lines = existing_notes.splitlines()
    if cleaned_note in existing_lines:
        return existing_notes

    return f"{existing_notes}\n{cleaned_note}"
