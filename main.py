"""Lance le serveur keep-alive (pour Render ou équivalent) puis le bot Discord."""
from keepalive import start_keepalive_server
from bot import bot
import config

if __name__ == "__main__":
    start_keepalive_server()

    if config.TOKEN:
        bot.run(config.TOKEN)
    else:
        print("❌ Erreur : la variable d'environnement DISCORD_TOKEN est introuvable.")
