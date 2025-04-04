import socket
import threading
import requests
import json
import time
import atexit
import argparse
import os

# === VÉRIFICATION DU FICHIER DE CONFIG ===
if not os.path.exists("config.json"):
    print("⚠️ Le fichier config.json n'existe pas. Création d'un fichier par défaut...")
    with open("config.json", "w") as f:
        json.dump({
            "username": "JoueurLocal",
            "port": 5555,
            "matchmaking_url": "https://rfosse.pythonanywhere.com"
        }, f, indent=2)
    print("✅ Fichier config.json créé. Veuillez le modifier avec vos informations.")

# === CHARGEMENT DE LA CONFIGURATION ===
with open("config.json") as f:
    config = json.load(f)

DEFAULT_PORT = config.get("port", 5555)
SERVER_URL = config.get("matchmaking_url", "https://rfosse.pythonanywhere.com")
USERNAME = config.get("username", "")

# === PARSER DE LIGNE DE COMMANDE ===
parser = argparse.ArgumentParser(description="Client local Bataille Navale")
parser.add_argument("--port", type=int, help="Port local à utiliser")
parser.add_argument("--username", type=str, help="Nom d'utilisateur")
args = parser.parse_args()

PORT = args.port if args.port else DEFAULT_PORT
if args.username:
    USERNAME = args.username

if not USERNAME or USERNAME == "JoueurLocal" or USERNAME == "YourUsername":
    USERNAME = input("👤 Entrez votre nom d'utilisateur: ").strip()
    config["username"] = USERNAME
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ Nom d'utilisateur '{USERNAME}' enregistré dans config.json")

# Variables globales
REGISTERED = False
socket_server = None

def get_public_ip():
    """Tente de récupérer l'adresse IP publique"""
    try:
        ip = requests.get("https://api.ipify.org").text
        print(f"🌍 Adresse IP publique: {ip}")
        return ip
    except:
        print("⚠️ Impossible de déterminer l'adresse IP publique.")
        return "127.0.0.1"

def auto_register():
    """Enregistre l'utilisateur sur le serveur de matchmaking"""
    global REGISTERED
    try:
        r = requests.post(f"{SERVER_URL}/auto_join", json={
            "username": USERNAME,
            "port": PORT
        })
        if r.status_code == 200:
            print(f"✅ Enregistré en tant que '{USERNAME}' sur le serveur")
            REGISTERED = True
            return True
        else:
            print("❌ Échec de l'enregistrement:", r.text)
            return False
    except Exception as e:
        print("❌ Impossible de joindre le serveur:", e)
        return False

def handle_match_request(message):
    """Traite une demande de match reçue"""
    try:
        data = json.loads(message)
        if "from" in data and "to" in data and data["to"] == USERNAME:
            challenger = data["from"]
            code = data.get("code")
            
            print(f"\n🔔 Demande de match de {challenger}" + (f" (code: {code})" if code else ""))
            response = input("Acceptez-vous le match? (oui/non): ").strip().lower()
            
            if response == "oui" or response == "o":
                try:
                    r = requests.post(f"{SERVER_URL}/confirm_match", json={
                        "player1": challenger,
                        "player2": USERNAME,
                        "code": code
                    })
                    if r.status_code == 200:
                        print("✅ Match accepté!")
                        # Lancer le jeu graphique
                        launch_game(challenger, code)
                    else:
                        print("⚠️ Impossible de confirmer le match:", r.text)
                except Exception as e:
                    print("❌ Échec de la confirmation du match:", e)
            else:
                print("❌ Match refusé.")
        else:
            print("⚠️ Format de message inconnu:", message)
    except json.JSONDecodeError:
        print("⚠️ Format de message invalide:", message)

def socket_listener():
    """Écoute les connexions entrantes pour les demandes de match"""
    global socket_server
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        socket_server.bind(("0.0.0.0", PORT))
        socket_server.listen(5)
        print(f"🔌 En écoute pour les demandes de match sur le port {PORT}...")
        
        while True:
            try:
                conn, addr = socket_server.accept()
                data = conn.recv(1024).decode()
                conn.close()
                
                if data:
                    print(f"📨 Message reçu de {addr}: {data[:50]}...")
                    handle_match_request(data)
            except Exception as e:
                print(f"⚠️ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur de socket: {e}")
    finally:
        if socket_server:
            socket_server.close()

def launch_game(opponent, match_code):
    """Lance le jeu graphique"""
    # Cette fonction peut lancer battleship_client.py avec les bons paramètres
    # Pour l'instant, affiche juste un message
    print(f"🎮 Lancement du jeu contre {opponent} avec le code {match_code}")
    print("📝 Veuillez lancer manuellement 'python battleship_client.py' et utiliser ce code.")

def create_match():
    """Crée un nouveau match et attend un adversaire"""
    code = input("Entrez un code de match (exemple: ABC123): ").strip()
    if not code:
        code = f"{USERNAME}_{int(time.time())}"
        print(f"🎲 Code de match généré: {code}")
    
    try:
        r = requests.post(f"{SERVER_URL}/create_match", json={
            "player_id": USERNAME,
            "code": code
        })
        if r.status_code == 200:
            print(f"📡 Match créé avec le code: {code}")
            print(f"📣 Partagez ce code avec votre adversaire!")
            print(f"⏳ En attente qu'un adversaire rejoigne le match...")
            
            # Attendre et vérifier si quelqu'un a rejoint
            for _ in range(60):  # 2 minutes d'attente maximum
                time.sleep(2)
                status = requests.get(f"{SERVER_URL}/match_status", params={"code": code})
                if status.status_code == 200:
                    data = status.json()
                    if data.get("status") == "active":
                        print(f"🎮 Match '{code}' démarré avec {data.get('opponent')}")
                        # Lancer le jeu
                        launch_game(data.get('opponent'), code)
                        return
                        
            print("⌛ Temps d'attente dépassé. Personne n'a rejoint votre match.")
        else:
            print("⚠️ Impossible de créer le match:", r.text)
    except Exception as e:
        print("❌ Erreur de création du match:", e)

def join_match():
    """Rejoint un match existant"""
    code = input("Entrez le code du match à rejoindre: ").strip()
    if not code:
        print("⚠️ Code requis.")
        return
        
    try:
        r = requests.post(f"{SERVER_URL}/join_match", json={
            "player_id": USERNAME,
            "code": code
        })
        if r.status_code == 200:
            data = r.json()
            players = data.get('players', [])
            
            if len(players) == 2:
                opponent = players[0] if players[1] == USERNAME else players[1]
                print(f"✅ Match rejoint! Vous jouez contre {opponent}")
                # Lancer le jeu
                launch_game(opponent, code)
            else:
                print("⚠️ Format de réponse inattendu du serveur.")
        else:
            print("⚠️ Impossible de rejoindre le match:", r.text)
    except Exception as e:
        print("❌ Erreur lors de la jonction au match:", e)

def match_result():
    """Soumet le résultat d'un match"""
    gagnant = input("Entrez le nom d'utilisateur du gagnant: ").strip()
    perdant = input("Entrez le nom d'utilisateur du perdant: ").strip()
    
    if not gagnant or not perdant:
        print("⚠️ Les noms du gagnant et du perdant sont requis.")
        return
        
    try:
        r = requests.post(f"{SERVER_URL}/match_result", json={
            "winner": gagnant,
            "loser": perdant
        })
        if r.status_code == 200:
            print("🏆 Résultat du match soumis avec succès!")
            print(f"🎊 {gagnant} a gagné contre {perdant}")
        else:
            print("⚠️ Impossible de soumettre le résultat:", r.text)
    except Exception as e:
        print("❌ Erreur lors de la soumission du résultat:", e)

def view_scoreboard():
    """Affiche le classement des joueurs"""
    try:
        r = requests.get(f"{SERVER_URL}/scores_history")
        if r.status_code == 200:
            data = r.json()
            scores = data.get('scores', [])
            
            print("\n🏆 CLASSEMENT DES JOUEURS")
            print("-------------------------")
            for i, (player, score) in enumerate(scores):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else " "
                print(f"{medal} {i+1}. {player}: {score} points")
            
            # Afficher l'historique des matches récents
            history = data.get('history', [])
            if history:
                print("\n📜 MATCHES RÉCENTS")
                print("-------------------------")
                for i, match in enumerate(history[-5:]):  # Afficher les 5 derniers matches
                    winner = match.get('winner', '?')
                    timestamp = match.get('timestamp', '?')
                    player1 = match.get('player1', '?')
                    player2 = match.get('player2', '?')
                    print(f"{i+1}. {timestamp}: {player1} vs {player2} → {winner}")
        else:
            print("⚠️ Impossible de récupérer le classement:", r.text)
    except Exception as e:
        print("❌ Erreur lors de la récupération du classement:", e)

def cleanup():
    """Nettoie les ressources avant de quitter"""
    if REGISTERED:
        try:
            requests.post(f"{SERVER_URL}/disconnect", json={"username": USERNAME})
            print("🚪 Déconnecté proprement du serveur.")
        except Exception as e:
            print("⚠️ Impossible de notifier le serveur:", e)
    
    if socket_server:
        try:
            socket_server.close()
        except:
            pass

# Enregistrer la fonction de nettoyage pour qu'elle soit appelée à la sortie
atexit.register(cleanup)

def main_menu():
    """Affiche le menu principal"""
    while True:
        print("\n🎮 BATAILLE NAVALE - MENU PRINCIPAL")
        print("-----------------------------------")
        print("1. 🆕 Créer un match")
        print("2. 🔍 Rejoindre un match")
        print("3. 🏆 Soumettre le résultat d'un match")
        print("4. 📊 Voir le classement")
        print("5. 🚪 Quitter")
        
        choix = input("\nChoisissez une action [1-5]: ").strip()
        
        if choix == "1":
            create_match()
        elif choix == "2":
            join_match()
        elif choix == "3":
            match_result()
        elif choix == "4":
            view_scoreboard()
        elif choix == "5":
            print("👋 Fermeture du client Bataille Navale.")
            break
        else:
            print("❌ Choix invalide. Veuillez réessayer.")

# === DÉMARRAGE ===
if __name__ == "__main__":
    print("🌊 BATAILLE NAVALE - CLIENT LOCAL")
    print("--------------------------------")
    print(f"👤 Utilisateur: {USERNAME}")
    print(f"🔌 Port: {PORT}")
    print(f"🌐 Serveur: {SERVER_URL}")
    
    # Enregistrer sur le serveur
    if auto_register():
        # Démarrer le thread d'écoute des demandes de match
        threading.Thread(target=socket_listener, daemon=True).start()
        # Afficher le menu principal
        main_menu()
    else:
        print("❌ Impossible de se connecter au serveur. Vérifiez votre connexion internet.")