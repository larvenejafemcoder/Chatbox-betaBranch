import json
import os
import textwrap
from datetime import datetime
from chatbox import ascii_box

BOX_WIDTH = 60
USER_FILE = "user.json"
MEMORY_FILE = "memory.json"


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def create_user():
    print(ascii_box(
        "[ SYSTEM ]",
        "No cadet profile detected.\nInitiating registration.",
        width=BOX_WIDTH
    ))
    name = input("Name: ")
    age = input("Age: ")
    study = input("Study Field: ")
    goal = input("Main Goal: ")

    user = {
        "name": name,
        "age": age,
        "study": study,
        "goal": goal,
        "rank": "Fresh Cadet",
        "xp": 0,
        "stress": 0,
        "messages": 0
    }
    save_json(USER_FILE, user)
    return user


def load_memory():
    memory = load_json(MEMORY_FILE)
    if memory is None:
        memory = {"facts": [], "conversation_log": []}
        save_json(MEMORY_FILE, memory)
    return memory


def remember(memory, fact):
    memory["facts"].append(fact)
    save_json(MEMORY_FILE, memory)


def update_rank(user):
    xp = user["xp"]
    if xp >= 1000:
        user["rank"] = "Commander"
    elif xp >= 700:
        user["rank"] = "Captain"
    elif xp >= 400:
        user["rank"] = "Lieutenant"
    elif xp >= 200:
        user["rank"] = "Sergeant"
    elif xp >= 100:
        user["rank"] = "Cadet"
    else:
        user["rank"] = "Fresh Cadet"


def status_panel(user):
    xp = user["xp"]
    bars = min(xp // 10, 10)
    xp_bar = "█" * bars + "░" * (10 - bars)
    content = (
        f"CADET : {user['name']}\n"
        f"RANK  : {user['rank']}\n"
        f"XP    : {xp_bar} {xp}\n"
        f"FIELD : {user['study']}\n"
        f"GOAL  : {user['goal']}"
    )
    print(ascii_box("[ CADET STATUS ]", content, width=BOX_WIDTH))


def ai_response(user, memory, msg):
    msg_lower = msg.lower()

    user["xp"] += 5
    user["messages"] += 1

    if "math" in msg_lower:
        user["xp"] += 10
        return (
            "Mathematical activity detected.\n"
            "Cognitive pathways responding positively.\n"
            "Recommendation: continue tactical calculations."
        )

    elif "python" in msg_lower or "code" in msg_lower:
        user["xp"] += 15
        return (
            "Programming discipline detected.\n"
            "Engineering potential increasing.\n"
            "System acknowledges technical growth."
        )

    elif "stress" in msg_lower or "tired" in msg_lower:
        user["stress"] += 1
        return (
            "Stress markers elevated.\n"
            "Recommend hydration and reduced overload.\n"
            "Cadet condition requires stabilization."
        )

    elif "study" in msg_lower:
        user["xp"] += 8
        return (
            "Study protocol acknowledged.\n"
            "Consistency builds tactical intelligence.\n"
            "Momentum is more important than intensity."
        )

    elif msg_lower.startswith("remember "):
        fact = msg[9:]
        remember(memory, fact)
        return f"Memory updated successfully.\nStored fact: {fact}"

    elif msg_lower == "memory":
        facts = memory["facts"]
        if not facts:
            return "Memory banks are currently empty."
        return "\n".join(f"- {x}" for x in facts)

    elif msg_lower == "status":
        return (
            f"Rank: {user['rank']}\n"
            f"XP: {user['xp']}\n"
            f"Stress: {user['stress']}\n"
            f"Messages: {user['messages']}"
        )

    else:
        responses = [
            "Command received.",
            "Processing cognitive request.",
            "System acknowledges your input.",
            "Cadet activity recorded.",
            "Awaiting next directive."
        ]
        return responses[user["messages"] % len(responses)]


def main():
    user = load_json(USER_FILE)
    if user is None:
        user = create_user()

    memory = load_memory()

    print()
    print(ascii_box(
        "[ KRNL COMMAND SYSTEM ]",
        f"Welcome back, {user['name']}.\nRank: {user['rank']}",
        width=BOX_WIDTH
    ))
    print()
    status_panel(user)

    while True:
        print()
        user_input = input("YOU > ")

        if user_input.lower() in ["exit", "quit"]:
            save_json(USER_FILE, user)
            print()
            print(ascii_box(
                "[ SYSTEM ]",
                "Session terminated.\nProgress saved successfully.",
                width=BOX_WIDTH
            ))
            break

        response = ai_response(user, memory, user_input)
        update_rank(user)
        save_json(USER_FILE, user)

        memory["conversation_log"].append({
            "time": str(datetime.now()),
            "user": user_input,
            "ai": response
        })
        save_json(MEMORY_FILE, memory)

        print()
        print(ascii_box("[ AI RESPONSE ]", response, width=BOX_WIDTH))
