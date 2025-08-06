from chatbox import PookieGPT
import time

def main():
    bot = PookieGPT()

    bot.intro() #Introduce thyself
    bot.user_name()      # Ask for name
    bot.general_quest()  # Mood check
    bot.whatodo()



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nPookieGPT: Wait— you ragequit on me?! Rude. 💔")
