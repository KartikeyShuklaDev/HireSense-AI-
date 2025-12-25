import os
from pathlib import Path


def save_audio_file(file_storage, save_path: Path):
    """
    Save uploaded audio file (Flask request.files['audio']) to disk.
    """
    os.makedirs(save_path.parent, exist_ok=True)
    file_storage.save(str(save_path))
    return str(save_path)
