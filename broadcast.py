import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Bot

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = os.environ.get("TOKEN")
LOCK_FILE = "broadcast_termine.lock"

# 1. Mini-serveur Flask (requis pour Render, mais cette fois il sert juste de borne de repos une fois fini)
app = Flask('')

@app.route('/')
def home():
    if os.path.exists(LOCK_FILE):
        return "Broadcast terminé et verrouillé avec succès. Aucune action en cours."
    return "Serveur de broadcast en cours d'exécution..."

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 2. Le script de diffusion ultra-sécurisé avec arrêt automatique et anti-boucle
async def run_broadcast():
    # SÉCURITÉ ABSOLUE : Si le fichier lock existe, on refuse catégoriquement de relancer
    if os.path.exists(LOCK_FILE):
        logging.warning("🛑 ARRÊT IMMÉDIAT : Le fichier verrou 'broadcast_termine.lock' existe. Le broadcast a déjà été effectué par le passé. Aucune action ne sera relancée pour éviter le spam.")
        return

    if not TOKEN:
        logging.error("Aucun TOKEN trouvé dans les variables d'environnement.")
        return

    bot = Bot(token=TOKEN)

    subscribers_file = "liste_abonnes.txt"
    if not os.path.exists(subscribers_file):
        logging.error(f"Le fichier {subscribers_file} est introuvable. Impossible de lancer le broadcast.")
        return

    with open(subscribers_file, "r", encoding="utf-8") as f:
        user_ids = [line.strip() for line in f if line.strip()]

    total = len(user_ids)
    if total == 0:
        logging.info("Aucun abonné trouvé dans la liste.")
        return

    message_file = "message.txt"
    if not os.path.exists(message_file):
        logging.error(f"Le fichier {message_file} est introuvable. Impossible de lancer le broadcast.")
        return

    with open(message_file, "r", encoding="utf-8") as f:
        message_text = f.read().strip()

    if not message_text:
        logging.error("Le message de diffusion est vide.")
        return

    logging.info(f"--- DÉBUT DU BROADCAST UNIQUE VERS {total} UTILISATEURS ---")

    success = 0
    blocked = 0
    
    BATCH_SIZE = 500      # Paquets de 500
    WAVE_PAUSE = 30       # 30 secondes de pause entre les vagues

    for i in range(0, total, BATCH_SIZE):
        batch = user_ids[i:i + BATCH_SIZE]
        wave_num = (i // BATCH_SIZE) + 1
        total_waves = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        logging.info(f"🚀 Vague {wave_num}/{total_waves} en cours ({len(batch)} utilisateurs)...")

        for uid in batch:
            try:
                await bot.send_message(
                    chat_id=int(uid), 
                    text=message_text, 
                    parse_mode="Markdown"
                )
                success += 1
                await asyncio.sleep(0.05) # Anti-flood individuel
            except Exception as e:
                blocked += 1
                logging.warning(f"Échec pour {uid}: {e}")

        # Pause entre les vagues (sauf pour la dernière)
        if i + BATCH_SIZE < total:
            logging.info(f"⏸️ Vague {wave_num} terminée. Pause de sécurité de {WAVE_PAUSE} secondes...")
            await asyncio.sleep(WAVE_PAUSE)

    logging.info("--- FIN DÉFINITIVE DU BROADCAST ---")
    logging.info(f"Bilan final -> Succès : {success} | Échecs (bloqués/supprimés) : {blocked}")

    # VERROUILLAGE : On crée le fichier témoin pour interdire à tout jamais un second lancement
    with open(LOCK_FILE, "w") as lock:
        lock.write("Broadcast completed successfully.")
    logging.info("🔒 Verrou activé : Fichier 'broadcast_termine.lock' généré. Le serveur restera en vie pour Render mais ne fera plus jamais de broadcast.")

def main():
    keep_alive()
    # Exécution unique du broadcast
    asyncio.run(run_broadcast())
    
    # Une fois fini, le script principal se bloque ici indéfiniment en gardant Flask actif 
    # (ce qui satisfait Render), mais la fonction run_broadcast ne se relancera plus grâce au verrou.
    import time
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
