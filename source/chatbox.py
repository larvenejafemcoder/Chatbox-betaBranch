from slow_print import *
import json
import random

gpt_name = "PookieGPT"
name = gpt_name

class Chat:
    def __init__(self, delay=(0.03, 0.08)):
        self.name = name
        self.delay = delay

    def chat(self, message):
        slow_print(f"{self.name}: {message}", self.delay)

    def input(self, message):
        return slow_input(f"{self.name}: {message}", self.delay)


'-----------------------------------------------------------------------------------------------------------------------------------'
with open("responds.json", "r", encoding="utf-8") as f:
    responds = json.load(f)

def general_quest():
    health = slow_input(random.choice(responds["greeting"])).strip()
    if health == "1":
        slow_print("Yay! I'm happy you're doing well.")
    elif health == "2":
        slow_print("Hmm, neutral vibe... wanna talk more?")
    elif health == "3":
        slow_print("Aww... sending virtual hugs 🫂")
    else:
        slow_print("I couldn't tell how you're feeling, but I'm here anyway.")




# def general_quest():
#     health = slow_input(f"{name}:How is your day?\n 1. It's good\n 2. Fine I guess\n 3. Not really good lmao\n").strip()
#     if health == "1":
#         slow_print("Yay! I'm happy you're doing well.")
#     elif health == "2":
#         slow_print("Hmm, neutral vibe... wanna talk more?")
#     elif health == "3":
#         slow_print("Aww... sending virtual hugs 🫂")
#     else:
#         slow_print("I couldn't tell how you're feeling, but I'm here anyway.")

def user_name():
    username = slow_input(f"{name}:Okay! What is your name?\nMy name is: ")
    slow_print(f"Okay, hello {username}!")

bot = Chat()