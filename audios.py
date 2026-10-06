"""Entrada, seleção e reprodução de áudio do trabalho."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional

_pygame_mixer = None
_audio_process = None


def _play_with_pygame(audio_path: Path) -> bool:
    """Toca formatos como MP3 pelo mixer do pygame sem bloquear a GUI."""
    global _pygame_mixer
    try:
        import pygame
        if _pygame_mixer is None:
            pygame.mixer.init()
            _pygame_mixer = pygame.mixer
        _pygame_mixer.music.load(str(audio_path))
        _pygame_mixer.music.play()
        return True
    except Exception:
        return False


def stop_music() -> None:
    """Para imediatamente a música atualmente reproduzida."""
    global _audio_process
    if _pygame_mixer is not None:
        try:
            _pygame_mixer.music.stop()
        except Exception:
            pass
    if _audio_process is not None:
        try:
            if _audio_process.poll() is None:
                _audio_process.terminate()
        except OSError:
            pass
        _audio_process = None


def _start_process(args: list[str]) -> bool:
    """Inicia um reprodutor externo e guarda o processo para poder pará-lo."""
    global _audio_process
    try:
        _audio_process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        _audio_process = None
        return False


def play_music(path: Optional[str]) -> bool:
    """Inicia a reprodução sem bloquear a interface."""
    if not path:
        return False
    audio_path = Path(path).expanduser().resolve()
    if not audio_path.is_file():
        return False

    stop_music()
    if _play_with_pygame(audio_path):
        return True

    system = platform.system()
    if system == "Windows":
        player = shutil.which("ffplay") or shutil.which("vlc") or shutil.which("wmplayer")
        if player:
            name = Path(player).name.lower()
            if name.startswith("ffplay"):
                args = [player, "-nodisp", "-autoexit", "-loglevel", "error", str(audio_path)]
            elif name.startswith("vlc"):
                args = [player, "--play-and-exit", "--intf", "dummy", str(audio_path)]
            else:
                args = [player, str(audio_path)]
            if _start_process(args):
                return True
        try:
            os.startfile(str(audio_path))  # type: ignore[attr-defined]
            return True
        except OSError:
            return False

    player = shutil.which("ffplay") or shutil.which("aplay") or shutil.which("paplay")
    if player:
        args = ([player, "-nodisp", "-autoexit", "-loglevel", "error", str(audio_path)]
                if os.path.basename(player) == "ffplay" else [player, str(audio_path)])
        thread = threading.Thread(target=_start_process, args=(args,), daemon=True)
        thread.start()
        return True
    return False
