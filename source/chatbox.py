import textwrap
import time
import random
import sys
from random import choice
import os
import re
import logging
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


# ─── ELIZA ENGINE ───────────────────────────────────────────────────

log = logging.getLogger(__name__)


class Key:
    def __init__(self, word, weight, decomps):
        self.word = word
        self.weight = weight
        self.decomps = decomps


class Decomp:
    def __init__(self, parts, save, reasmbs):
        self.parts = parts
        self.save = save
        self.reasmbs = reasmbs
        self.next_reasmb_index = 0


class Eliza:
    def __init__(self):
        self.initials = []
        self.finals = []
        self.quits = []
        self.pres = {}
        self.posts = {}
        self.synons = {}
        self.keys = {}
        self.memory = []

    def load(self, path):
        key = None
        decomp = None
        with open(path) as file:
            for line in file:
                if not line.strip():
                    continue
                tag, content = [part.strip() for part in line.split(':')]
                if tag == 'initial':
                    self.initials.append(content)
                elif tag == 'final':
                    self.finals.append(content)
                elif tag == 'quit':
                    self.quits.append(content)
                elif tag == 'pre':
                    parts = content.split(' ')
                    self.pres[parts[0]] = parts[1:]
                elif tag == 'post':
                    parts = content.split(' ')
                    self.posts[parts[0]] = parts[1:]
                elif tag == 'synon':
                    parts = content.split(' ')
                    self.synons[parts[0]] = parts
                elif tag == 'key':
                    parts = content.split(' ')
                    word = parts[0]
                    weight = int(parts[1]) if len(parts) > 1 else 1
                    key = Key(word, weight, [])
                    self.keys[word] = key
                elif tag == 'decomp':
                    parts = content.split(' ')
                    save = False
                    if parts[0] == '$':
                        save = True
                        parts = parts[1:]
                    decomp = Decomp(parts, save, [])
                    key.decomps.append(decomp)
                elif tag == 'reasmb':
                    parts = content.split(' ')
                    decomp.reasmbs.append(parts)

    def _match_decomp_r(self, parts, words, results):
        if not parts and not words:
            return True
        if not parts or (not words and parts != ['*']):
            return False
        if parts[0] == '*':
            for index in range(len(words), -1, -1):
                results.append(words[:index])
                if self._match_decomp_r(parts[1:], words[index:], results):
                    return True
                results.pop()
            return False
        elif parts[0].startswith('@'):
            root = parts[0][1:]
            if not root in self.synons:
                raise ValueError("Unknown synonym root {}".format(root))
            if not words[0].lower() in self.synons[root]:
                return False
            results.append([words[0]])
            return self._match_decomp_r(parts[1:], words[1:], results)
        elif parts[0].lower() != words[0].lower():
            return False
        else:
            return self._match_decomp_r(parts[1:], words[1:], results)

    def _match_decomp(self, parts, words):
        results = []
        if self._match_decomp_r(parts, words, results):
            return results
        return None

    def _next_reasmb(self, decomp):
        index = decomp.next_reasmb_index
        result = decomp.reasmbs[index % len(decomp.reasmbs)]
        decomp.next_reasmb_index = index + 1
        return result

    def _reassemble(self, reasmb, results):
        output = []
        for reword in reasmb:
            if not reword:
                continue
            if reword[0] == '(' and reword[-1] == ')':
                index = int(reword[1:-1])
                if index < 1 or index > len(results):
                    raise ValueError("Invalid result index {}".format(index))
                insert = results[index - 1]
                for punct in [',', '.', ';']:
                    if punct in insert:
                        insert = insert[:insert.index(punct)]
                output.extend(insert)
            else:
                output.append(reword)
        return output

    def _sub(self, words, sub):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower in sub:
                output.extend(sub[word_lower])
            else:
                output.append(word)
        return output

    def _match_key(self, words, key):
        for decomp in key.decomps:
            results = self._match_decomp(decomp.parts, words)
            if results is None:
                log.debug('Decomp did not match: %s', decomp.parts)
                continue
            log.debug('Decomp matched: %s', decomp.parts)
            log.debug('Decomp results: %s', results)
            results = [self._sub(words, self.posts) for words in results]
            log.debug('Decomp results after posts: %s', results)
            reasmb = self._next_reasmb(decomp)
            log.debug('Using reassembly: %s', reasmb)
            if reasmb[0] == 'goto':
                goto_key = reasmb[1]
                if not goto_key in self.keys:
                    raise ValueError("Invalid goto key {}".format(goto_key))
                log.debug('Goto key: %s', goto_key)
                return self._match_key(words, self.keys[goto_key])
            output = self._reassemble(reasmb, results)
            if decomp.save:
                self.memory.append(output)
                log.debug('Saved to memory: %s', output)
                continue
            return output
        return None

    def respond(self, text):
        if text.lower() in self.quits:
            return None

        text = re.sub(r'\s*\.+\s*', ' . ', text)
        text = re.sub(r'\s*,+\s*', ' , ', text)
        text = re.sub(r'\s*;+\s*', ' ; ', text)
        log.debug('After punctuation cleanup: %s', text)

        words = [w for w in text.split(' ') if w]
        log.debug('Input: %s', words)

        words = self._sub(words, self.pres)
        log.debug('After pre-substitution: %s', words)

        keys = [self.keys[w.lower()] for w in words if w.lower() in self.keys]
        keys = sorted(keys, key=lambda k: -k.weight)
        log.debug('Sorted keys: %s', [(k.word, k.weight) for k in keys])

        output = None

        for key in keys:
            output = self._match_key(words, key)
            if output:
                log.debug('Output from key: %s', output)
                break
        if not output:
            if self.memory:
                index = random.randrange(len(self.memory))
                output = self.memory.pop(index)
                log.debug('Output from memory: %s', output)
            else:
                output = self._next_reasmb(self.keys['xnone'].decomps[0])
                log.debug('Output from xnone: %s', output)

        return " ".join(output)

    def initial(self):
        return random.choice(self.initials)

    def final(self):
        return random.choice(self.finals)

    def run(self):
        print(self.initial())

        while True:
            sent = input('> ')

            output = self.respond(sent)
            if output is None:
                break

            print(output)

        print(self.final())


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
