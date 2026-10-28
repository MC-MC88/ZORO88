import os
import re
import json
import time
import queue
import difflib
import threading
import urllib.request
import zipfile
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import yaml

import actions
from app_scanner import get_installed_apps

if getattr(sys, 'frozen', False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent

PHRASES = BASE / "phrases"
MODEL_DIR = BASE / "vosk-model-small-en-us-0.15"
COMMANDS_FILE = BASE / "commands.yaml"

WAKE_WORD = "zoro"
SLEEP_TIMEOUT = 300
SAMPLE_RATE = 16000
BLOCK_SIZE = 4000

_playing = threading.Event()
_state = {
    "is_awake": False,
    "last_interaction": 0.0,
    "pending_action": None,
    "pending_deadline": 0.0,
}
_commands = None
_installed_apps = {}
_audio_queue = queue.Queue()
_ui_callback = None

_FALLBACK_TEXT = {
    "ready": "Ready.",
    "done": "Done.",
    "confirm": "Are you sure? Say yes or no.",
    "cancelled": "Cancelled.",
    "sorry": "Sorry, I didn't catch that.",
    "sleep": "Going to sleep."
}

def _audio_player_thread():
    while True:
        phrase_name = _audio_queue.get()
        if phrase_name is None: break
        path = PHRASES / f"{phrase_name}.mp3"
        if path.exists():
            try:
                data, sr = sf.read(str(path))
                sd.play(data, sr)
                sd.wait()
            except Exception: pass
        else:
            print(f"  [tts] {_FALLBACK_TEXT.get(phrase_name, phrase_name)}")
        _audio_queue.task_done()
        time.sleep(0.2)
        _playing.clear()

threading.Thread(target=_audio_player_thread, daemon=True).start()

def play_phrase(name):
    _playing.set()
    _audio_queue.put(name)
    if _ui_callback: _ui_callback(f"Speaking: {_FALLBACK_TEXT.get(name, name)}")

def ensure_model():
    if MODEL_DIR.is_dir() and any(MODEL_DIR.iterdir()): return
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    tmp = BASE / "vosk.zip"
    urllib.request.urlretrieve(url, tmp)
    with zipfile.ZipFile(tmp, "r") as z: z.extractall(BASE)
    tmp.unlink()

def load_commands():
    with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["commands"]

def match_command(text):
    text_l = text.lower().strip()
    best = None
    best_score = 0.0
    for cmd in _commands:
        for pattern in cmd["patterns"]:
            score = difflib.SequenceMatcher(None, text_l, pattern.lower()).ratio()
            if score > best_score and score >= 0.75:
                best = cmd
                best_score = score
    return best

def execute_action(name):
    fn = getattr(actions, name, None)
    if not fn:
        play_phrase("sorry")
        return
    try:
        result = fn()
        if isinstance(result, str): play_phrase(result)
        else: play_phrase("done")
    except Exception:
        play_phrase("sorry")

def process_text(text):
    text = text.lower().strip()
    if not text: return
    
    if _ui_callback: _ui_callback(f"Heard: {text}")
    
    now = time.time()

    if _state["pending_action"]:
        if now >= _state["pending_deadline"]:
            _state["pending_action"] = None
            play_phrase("cancelled")
            return
        if any(w in text for w in ("yes", "yeah", "confirm")):
            action = _state["pending_action"]
            _state["pending_action"] = None
            execute_action(action)
            return
        if any(w in text for w in ("no", "cancel")):
            _state["pending_action"] = None
            play_phrase("cancelled")
            return
        return

    if not _state["is_awake"]:
        if "zoro" in text and ("wake" in text or "up" in text or "week" in text):
            _state["is_awake"] = True
            _state["last_interaction"] = now
            play_phrase("ready")
            if _ui_callback: _ui_callback("Status: Awake")
        return

    _state["last_interaction"] = now

    if text.startswith("open "):
        app_query = text[5:].strip()
        best_app = None
        best_score = 0.0
        for app_name, app_path in _installed_apps.items():
            score = difflib.SequenceMatcher(None, app_query, app_name).ratio()
            if score > best_score and score >= 0.75:
                best_app = app_path
                best_score = score
        
        if best_app and actions.open_app(best_app):
            play_phrase("done")
        else:
            play_phrase("sorry")
        return

    if text.startswith("close "):
        app_query = text[6:].strip()
        if app_query in ("all windows", "everything"):
            _state["pending_action"] = "force_close_all_windows"
            _state["pending_deadline"] = now + 5.0
            play_phrase("confirm")
            return
        else:
            play_phrase("done")
        return

    cmd = match_command(text)
    if not cmd:
        play_phrase("sorry")
        return

    action_name = cmd["action"]
    if cmd.get("confirm", False):
        _state["pending_action"] = action_name
        _state["pending_deadline"] = now + 5.0
        play_phrase("confirm")
        return

    if action_name == "set_theme_light": actions.set_theme("light")
    elif action_name == "set_theme_dark": actions.set_theme("dark")
    else: execute_action(action_name)
    
    if _ui_callback: _ui_callback(f"Action: {action_name}")

def main_loop(ui_callback):
    global _commands, _installed_apps, _ui_callback
    _ui_callback = ui_callback
    
    ensure_model()
    import vosk
    vosk.SetLogLevel(-1)
    _model = vosk.Model(str(MODEL_DIR))
    _commands = load_commands()
    _installed_apps = get_installed_apps()

    audio_q = queue.Queue()
    def _cb(indata, frames, t, status): audio_q.put(bytes(indata))

    rec = vosk.KaldiRecognizer(_model, SAMPLE_RATE)
    was_playing = False

    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=BLOCK_SIZE, callback=_cb):
        while True:
            chunk = audio_q.get()
            if _playing.is_set():
                was_playing = True
                continue
            if was_playing:
                rec = vosk.KaldiRecognizer(_model, SAMPLE_RATE)
                was_playing = False

            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text: process_text(text)

            if _state["is_awake"] and time.time() - _state["last_interaction"] > SLEEP_TIMEOUT:
                _state["is_awake"] = False
                play_phrase("sleep")
                if _ui_callback: _ui_callback("Status: Sleeping")
