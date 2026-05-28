import textwrap
import time
import random
import sys
from random import choice
import os
from slow_print import slow_print
from ranking import RankingSystem
import json

gpt_name = "PookieGPT"
dev_name = "Larvene Jafem"

# ─── VN ASCII BOX SYSTEM ────────────────────────────────────────────

DEFAULT_BOX_WIDTH = 54


def _wrap_lines(text, width):
    lines = []
    for line in text.split("\n"):
        wrapped = textwrap.wrap(line, width=width)
        lines.extend(wrapped or [""])
    return lines


def ascii_box(title, content, width=DEFAULT_BOX_WIDTH):
    inner = width - 4
    top = "┌" + "─" * (width - 2) + "┐"
    mid = "├" + "─" * (width - 2) + "┤"
    bot = "└" + "─" * (width - 2) + "┘"
    lines = _wrap_lines(content, inner)
    result = [top, f"│ {title:<{inner}} │", mid]
    result.extend(f"│ {line:<{inner}} │" for line in lines)
    result.append(bot)
    return "\n".join(result)


def status_panel(user_data):
    rank = user_data.get("rank", "Fresh Cadet")
    xp = min(user_data.get("xp", 0), 100)
    name = user_data.get("name", "Unknown")
    study = user_data.get("study", "Undeclared")
    filled = xp // 10
    bar = "█" * filled + "░" * (10 - filled)
    content = (
        f"CADET : {name}\n"
        f"RANK  : {rank}\n"
        f"STUDY : {study}\n"
        f"XP    : {bar} {xp}/100"
    )
    return ascii_box("[ CADET STATUS ]", content)


def ai_response(message):
    return ascii_box("[ SYSTEM RESPONSE ]", message)


def warning_panel(message):
    return ascii_box("[ WARNING ]", message)


def log_panel(event):
    now = time.strftime("%H:%M:%S")
    return ascii_box("[ SYSTEM LOG ]", f"{now} | {event}")


# ─── PookieGPT BOT ──────────────────────────────────────────────────

class PookieGPT:
    def __init__(self, name=gpt_name, delay=(0.01, 0.04)):
        self.name = name
        self.delay = delay

        file_path = os.path.join(os.path.dirname(__file__), "responses.json")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.responds = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ERROR] Could not load responses.json: {e}")
            self.responds = {}

    # ── Boxed output helpers ─────────────────────────────────────

    def _box_out(self, title, text):
        slow_print(ascii_box(title, text), self.delay)

    def _box_in(self, title, prompt_text):
        slow_print(ascii_box(title, prompt_text), self.delay)
        return input("> ").strip()

    # ── Introduction ──────────────────────────────────────────────

    def introduction(self, username):
        self._box_out("[ POOKIEGPT ]", choice(self.responds['introduction']))
        self._box_out("[ SYSTEM ]", "Hey boss, my name is PookieGPT!")

    # ── General Question / Mood Check ─────────────────────────────

    def general_quest(self):
        mood = self._box_in(
            "[ MOOD CHECK ]",
            choice(self.responds['greeting'])
        )
        mood_map = {"1": "1", "2": "2", "3": "3"}
        key = mood_map.get(mood)

        if not key and ("sad" in mood or "bad" in mood):
            key = "2"

        if key:
            response = choice(self.responds["health_responses"][key])
        else:
            response = "I couldn't tell how you're feeling, but I'm here anyway. 🌸"

        self._box_out("[ POOKIEGPT ]", response)

    # ── Rage Quit ─────────────────────────────────────────────────

    def rage_quit(self):
        self._box_out("[ SYSTEM ]", choice(self.responds['rage_quit']))

    # ── Legacy Shutdown ───────────────────────────────────────────

    def legacy_shutdown(self):
        self._box_out("[ SYSTEM ]", choice(self.responds['shutting_down']))

    # ── Continue Talking ──────────────────────────────────────────

    def con_talk(self):
        ask_line = choice(self.responds["talk"])
        continue_talk = self._box_in("[ POOKIEGPT ]", ask_line)

        category_map = {
            "1": "schoolwork_problem",
            "2": "debugging_problem",
            "3": "existential_problem"
        }

        category = category_map.get(continue_talk.strip())

        if continue_talk in category_map:
            self._box_out("[ POOKIEGPT ]", choice(self.responds[category]))
        else:
            self._box_out("[ WARNING ]", choice(self.responds['try_again']))
            self.legacy_shutdown()

    # ── Ask Me Question ───────────────────────────────────────────

    def askmeQuestion(self):
        user_q = self._box_in("[ POOKIEGPT ]", choice(self.responds['askPookie']))

        match user_q:
            case "1":
                self._box_out("[ POOKIEGPT ]", choice(self.responds['whatimfor']))
            case "2":
                self._box_out("[ POOKIEGPT ]", choice(self.responds['howispookie']))
            case "3":
                self._box_out("[ POOKIEGPT ]", choice(self.responds['jokes']))
            case "4":
                self._box_out(f"[ {dev_name.upper()} ]", choice(self.responds['whatslarvesjob']))
            case "5":
                self._box_out(f"[ {dev_name.upper()} ]", choice(self.responds['whymentalissue']))
            case "6":
                self._box_out("[ SYSTEM ]", "Rank commission: ACCESS DENIED")
            case _:
                self._box_out("[ WARNING ]", choice(self.responds['try_again']))

    # ── What to Do Next ───────────────────────────────────────────

    def whatodo(self):
        ask_line = choice(self.responds["what_to_do"])
        while True:
            whattodonow = self._box_in("[ MISSION ]", ask_line)
            if whattodonow == "1":
                bot.con_talk()
            elif whattodonow == "2":
                bot.askmeQuestion()
            elif whattodonow == "3":
                self._box_out("[ SYSTEM ]", choice(self.responds['goodbye']))
                break
            else:
                break


# ─── Initialize Bot ────────────────────────────────────────────────

bot = PookieGPT()
