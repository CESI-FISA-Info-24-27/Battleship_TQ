import socket
import threading
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NetworkingHelper")

class NetworkingHelper:
    """Classe utilitaire pour faciliter la gestion réseau du jeu"""
    
    @staticmethod
    def get_local_ip():
        """
        Obtenir l'adresse IP locale de la machine
        
        Returns:
            str: Adresse IP locale ou "127.0.0.1" en cas d'échec
        """
        try:
            # Méthode la plus fiable pour obtenir l'IP locale utilisée pour les connexions externes
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'IP locale: {e}")
            try:
                # Plan B: utiliser gethostbyname
                return socket.gethostbyname(socket.gethostname())
            except:
                # Plan C: parcourir les interfaces réseau
                try:
                    hostname = socket.gethostname()
                    for addrinfo in socket.getaddrinfo(hostname, None):
                        if addrinfo[0] == socket.AF_INET:
                            ip = addrinfo[4][0]
                            if not ip.startswith('127.'):
                                return ip
                except:
                    pass
                # En dernier recours, retourner localhost
                return "127.0.0.1"
    
    @staticmethod
    def get_public_ip():
        """
        Obtenir l'adresse IP publique de la connexion internet
        
        Returns:
            str: Adresse IP publique ou None en cas d'échec
        """
        try:
            # Essayer différents services pour obtenir l'IP publique
            # Option 1: ipify.org
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                return response.json()['ip']
                
            # Option 2: ifconfig.me (si ipify ne fonctionne pas)
            response = requests.get('https://ifconfig.me/ip', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'IP publique: {e}")
            return None
            
    @staticmethod
    def try_upnp_port_forward(port=65432, protocol='TCP', description="Bataille Navale"):
        """
        Tenter d'ouvrir un port sur le routeur via UPnP
        
        Args:
            port: Port à ouvrir
            protocol: Protocole (TCP/UDP)
            description: Description de la redirection
            
        Returns:
            (success, message): Tuple (booléen de réussite, message d'information)
        """
        try:
            import miniupnpc
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            
            # Découvrir les périphériques UPnP
            discovered_devices = upnp.discover()
            if discovered_devices == 0:
                return False, "Aucun périphérique UPnP trouvé"
                
            # Sélectionner la passerelle Internet
            upnp.selectigd()
            
            # Obtenir l'adresse IP locale
            local_ip = NetworkingHelper.get_local_ip()
            
            # Vérifier si le mapping existe déjà
            for i in range(upnp.getportmappingnumberofentries()):
                mapping = upnp.getgenericportmapping(i)
                if mapping and mapping[0] == port and mapping[1] == protocol:
                    return True, f"Le port {port} est déjà ouvert pour {mapping[2]}"
            
            # Essayer de mapper le port
            result = upnp.addportmapping(
                port, protocol, local_ip, port, description, ''
            )
            
            if result:
                logger.info(f"Port {port} ouvert avec succès via UPnP")
                return True, f"Port {port} ouvert avec succès"
            else:
                logger.warning(f"Échec de l'ouverture du port {port} via UPnP")
                return False, "Échec de l'ouverture du port"
                
        except ImportError:
            logger.warning("La bibliothèque miniupnpc n'est pas installée")
            return False, "miniupnpc non installé (pip install miniupnpc)"
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation d'UPnP: {e}")
            return False, f"Erreur UPnP: {str(e)}"
            
    @staticmethod
    def check_port_open(host, port=65432, timeout=2):
        """
        Vérifier si un port est ouvert sur un hôte
        
        Args:
            host: Adresse de l'hôte
            port: Port à vérifier
            timeout: Délai d'attente en secondes
            
        Returns:
            bool: True si le port est ouvert, False sinon
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du port {port} sur {host}: {e}")
            return False
            
    @staticmethod
    def port_forward_instructions():
        """
        Retourne des instructions pour la redirection manuelle des ports
        
        Returns:
            list: Liste de chaînes d'instructions
        """
        return [
            "Pour permettre les connexions depuis l'extérieur:",
            "1. Accédez à l'interface de votre routeur (généralement 192.168.0.1 ou 192.168.1.1)",
            "2. Trouvez la section 'Redirection de port' ou 'Port Forwarding'",
            "3. Créez une nouvelle règle pour rediriger le port 65432 (TCP) vers votre adresse IP locale",
            "4. Appliquez les changements et redémarrez le routeur si nécessaire"
        ]
        
    @staticmethod
    def test_public_connection(port=65432):
        """
        Tester si la connexion publique est possible
        
        Returns:
            (success, message): Tuple (booléen de réussite, message d'information)
        """
        local_ip = NetworkingHelper.get_local_ip()
        public_ip = NetworkingHelper.get_public_ip()
        
        if not public_ip:
            return False, "Impossible de déterminer l'IP publique"
            
        # Si l'IP locale et l'IP publique semblent identiques, nous sommes peut-être
        # directement connectés à Internet sans NAT
        if local_ip == public_ip:
            if NetworkingHelper.check_port_open(local_ip, port):
                return True, "Port accessible depuis l'extérieur"
            else:
                return False, "Le port semble être bloqué par un pare-feu"
                
        # Ici, nous devrions idéalement tester depuis un serveur externe
        # Mais comme nous ne pouvons pas le faire facilement, on renvoie une info
        return None, "Impossible de tester la connexion externe automatiquement"