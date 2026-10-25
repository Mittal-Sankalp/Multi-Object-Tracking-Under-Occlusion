"""
MarketQuest - Save & Load Manager
Safely persists player progress, market state, portfolio, and missions to JSON.
Employs atomic file replacement to prevent save file corruption.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import SAVES_DIR

SAVE_FILENAME = "savegame.json"

class SaveManager:
    def __init__(self, saves_dir: Optional[Path] = None):
        self.saves_dir = saves_dir or SAVES_DIR
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        self.save_path = self.saves_dir / SAVE_FILENAME

    def has_save(self) -> bool:
        return self.save_path.exists() and self.save_path.stat().st_size > 10

    def save_game(self, game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """Save game state atomically using a temp file."""
        try:
            self.saves_dir.mkdir(parents=True, exist_ok=True)
            # Write to temporary file in the same directory
            with tempfile.NamedTemporaryFile('w', dir=self.saves_dir, delete=False, encoding='utf-8') as tf:
                json.dump(game_state, tf, indent=2)
                temp_name = tf.name

            # Atomically replace destination file
            os.replace(temp_name, self.save_path)
            return True, "Game successfully saved!"
        except Exception as e:
            return False, f"Failed to save game: {str(e)}"

    def load_game(self) -> Optional[Dict[str, Any]]:
        """Load and parse saved game state with graceful error recovery."""
        if not self.has_save():
            return None
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception:
            return None

    def delete_save(self) -> bool:
        try:
            if self.save_path.exists():
                self.save_path.unlink()
            return True
        except Exception:
            return False
