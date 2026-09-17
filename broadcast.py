import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Bot

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Récupération sécurisée du Token
TOKEN = os.environ.get("TOKEN")

# 1. Mini-serveur web Flask obligatoire pour que Render valide l'offre gratuite (Web Service)
app = Flask('')

@app.route('/')
def home():
    return "Le service de broadcast Biglolo est en ligne !"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 2. Le script de diffusion asynchrone
async def run_broadcast():
    if not TOKEN:
        logging.error("Aucun TOKEN trouvé dans les variables d'environnement.")
        return

    bot = Bot(token=TOKEN)

    # Lecture de la liste des abonnés
    subscribers_file = "liste_abonnes.txt"
    if not os.path.exists(subscribers_file):
        logging.error(f"Le fichier {subscribers_file} est introuvable.")
        return

    with open(subscribers_file, "r", encoding="utf-8") as f:
        user_ids = [line.strip() for line in f if line.strip()]

    total = len(user_ids)
    if total == 0:
        logging.info("Aucun abonné trouvé dans la liste.")
        return

    # Lecture du message
    message_file = "message.txt"
    if not os.path.exists(message_file):
        logging.error(f"Le fichier {message_file} est introuvable.")
        return

    with open(message_file, "r", encoding="utf-8") as f:
        message_text = f.read().strip()

    if not message_text:
        logging.error("Le message de diffusion est vide.")
        return

    logging.info(f"--- DÉBUT DU BROADCAST VERS {total} UTILISATEURS ---")

    success = 0
    blocked = 0

    for uid in user_ids:
        try:
            await bot.send_message(
                chat_id=int(uid), 
                text=message_text, 
                parse_mode="Markdown"
            )
            success += 1
            await asyncio.sleep(0.05) # Pause anti-spam
        except Exception as e:
            blocked += 1
            logging.warning(f"Échec pour {uid}: {e}")

    logging.info("--- FIN DU BROADCAST ---")
    logging.info(f"Succès : {success} | Échecs : {blocked}")

def main():
    # Lance le mini-serveur web en arrière-plan pour satisfaire Render
    keep_alive()
    
    # Lance automatiquement le broadcast au démarrage du déploiement
    asyncio.run(run_broadcast())

if __name__ == "__main__":
    main()
