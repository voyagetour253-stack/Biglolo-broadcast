import os
import asyncio
from telegram import Bot

# Récupération sécurisée du Token du bot depuis les variables d'environnement de Render
TOKEN = os.environ.get("TOKEN")

async def run_broadcast():
    if not TOKEN:
        print("Erreur : Aucun TOKEN trouvé dans les variables d'environnement.")
        return

    bot = Bot(token=TOKEN)

    # 1. Lecture de la liste des abonnés
    subscribers_file = "liste_abonnes.txt"
    if not os.path.exists(subscribers_file):
        print(f"Erreur : Le fichier {subscribers_file} est introuvable.")
        return

    with open(subscribers_file, "r", encoding="utf-8") as f:
        # Nettoie les espaces et ignore les lignes vides
        user_ids = [line.strip() for line in f if line.strip()]

    total = len(user_ids)
    if total == 0:
        print("Aucun abonné trouvé dans la liste.")
        return

    # 2. Lecture du message à diffuser
    message_file = "message.txt"
    if not os.path.exists(message_file):
        print(f"Erreur : Le fichier {message_file} est introuvable.")
        return

    with open(message_file, "r", encoding="utf-8") as f:
        message_text = f.read().strip()

    if not message_text:
        print("Erreur : Le message de diffusion est vide.")
        return

    print(f"--- DÉBUT DU BROADCAST VERS {total} UTILISATEURS ---")

    success = 0
    blocked = 0

    # 3. Boucle d'envoi avec protection anti-blocage
    for uid in user_ids:
        try:
            await bot.send_message(
                chat_id=int(uid), 
                text=message_text, 
                parse_mode="Markdown"
            )
            success += 1
            # Pause de sécurité pour respecter les limites de Telegram
            await asyncio.sleep(0.05)
        except Exception as e:
            # Si le compte a bloqué le bot ou n'existe pas
            blocked += 1
            print(f"Échec pour {uid}: {e}")

    print("--- FIN DU BROADCAST ---")
    print(f"Succès : {success}")
    print(f"Échecs (comptes bloqués / introuvables) : {blocked}")

if __name__ == "__main__":
    asyncio.run(run_broadcast())