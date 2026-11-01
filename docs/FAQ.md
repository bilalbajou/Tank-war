# ❓ Foire Aux Questions & Dépannage (FAQ) — TANK WAR

Ce document répertorie les problèmes techniques et réseau les plus fréquemment rencontrés, leurs causes racines et leurs solutions pas-à-pas.

---

## 📑 Sommaire
1. [Problèmes de Connexion Réseau](#1-problèmes-de-connexion-réseau)
   - [Le client ne trouve pas le serveur (Hôte introuvable)](#11-le-client-ne-trouve-pas-le-serveur)
   - [Erreur « Connection Refused »](#12-erreur--connection-refused-)
   - [Erreur « Connection Timeout » (Délai d'attente dépassé)](#13-erreur--connection-timeout-)
   - [Adresse IP incorrecte ou masque de sous-réseau différent](#14-adresse-ip-incorrecte-ou-masque-de-sous-réseau-différent)
   - [Port TCP bloqué par le Pare-feu Windows Defender](#15-port-tcp-bloqué-par-le-pare-feu-windows-defender)
   - [Les deux PC ne sont pas sur le même réseau local](#16-les-deux-pc-ne-sont-pas-sur-le-même-réseau-local)
   - [Conflits causés par un logiciel VPN](#17-conflits-causés-par-un-logiciel-vpn)
2. [Déconnexions et Stabilité en Jeu](#2-déconnexions-et-stabilité-en-jeu)
   - [Déconnexion inattendue d'un joueur pendant la partie](#21-déconnexion-inattendue-dun-joueur-pendant-la-partie)
   - [Problèmes de désynchronisation ou de saccades (Lag)](#22-problèmes-de-désynchronisation-ou-de-saccades-lag)
   - [Le jeu se ferme brusquement (Crash)](#23-le-jeu-se-ferme-brusquement-crash)
3. [Problèmes Audiovisuels et Système](#3-problèmes-audiovisuels-et-système)
   - [Aucun son ou mixer Pygame inactif](#31-aucun-son-ou-mixer-pygame-inactif)
   - [Erreur d'installation de Pygame sous Python 3.14](#32-erreur-dinstallation-de-pygame-sous-python-314)

---

## 1. Problèmes de Connexion Réseau

### 1.1 Le client ne trouve pas le serveur
* **Symptômes** : L'écran de connexion du Joueur 2 affiche le statut clignotant *"Connexion en cours..."* puis bascule sur *"Impossible de joindre l'hôte (Vérifiez l'adresse IP et le Wi-Fi)"*.
* **Causes Possibles** :
  1. Le serveur hôte n'a pas encore été lancé sur le PC 1.
  2. L'adresse IP saisie ne correspond pas à l'adresse de la carte Wi-Fi du PC 1.
  3. Le pare-feu de Windows bloque les paquets TCP entrants sur le port 4242.
* **Solutions** :
  - Assurez-vous que le PC 1 a bien cliqué sur **`📡 HÉBERGER UNE PARTIE`** (ou a lancé `python main.py --host`) et affiche l'écran d'attente.
  - Vérifiez l'adresse IPv4 affichée sur l'écran du PC 1 (ex: `192.168.1.45`) et recopiez-la fidèlement sur le PC 2.
  - Consultez la section [1.5 sur le Pare-feu](#15-port-tcp-bloqué-par-le-pare-feu-windows-defender).

---

### 1.2 Erreur « Connection Refused »
* **Symptômes** : Le client tente de se connecter et est immédiatement rejeté en une fraction de seconde.
* **Causes Possibles** :
  1. Aucun processus n'écoute sur le port spécifié (ex: le serveur n'est pas démarré ou écoute sur un autre port).
  2. Deux joueurs sont déjà connectés dans la partie : le serveur rejette tout 3ᵉ joueur pour respecter la règle stricte du duel à 2.
* **Solutions** :
  - Vérifiez le port utilisé : par défaut, le jeu utilise le port `4242`. Si l'hôte a lancé le jeu avec `--port 5555`, le client doit impérativement préciser `--join 192.168.1.XX:5555`.
  - Si une ancienne partie a été mal fermée, quittez complètement la fenêtre du jeu sur le PC 1 et relancez-le.

---

### 1.3 Erreur « Connection Timeout »
* **Symptômes** : La tentative de connexion dure environ 3 à 4 secondes avant d'échouer sans aucune réponse.
* **Causes Possibles** :
  1. Le pare-feu du PC 1 ignore silencieusement les paquets SYN entrants.
  2. L'option **AP Isolation** (Isolation des points d'accès) est activée sur votre box Wi-Fi (très courant sur les réseaux "Wi-Fi Invité").
* **Solutions** :
  - Sur le PC 1, autorisez le port TCP 4242 dans le Pare-feu Windows (voir commande PowerShell en section 1.5).
  - Connectez les deux ordinateurs au Wi-Fi privé principal de la box, ou basculez sur un **Partage de connexion mobile** via smartphone.

---

### 1.4 Adresse IP incorrecte ou masque de sous-réseau différent
* **Symptômes** : Les deux PC semblent connectés à Internet, mais le client ne parvient jamais à contacter l'hôte.
* **Causes Possibles** :
  - Le PC 1 a renseigné l'adresse de sa carte Ethernet filaire ou d'une carte virtuelle (VirtualBox, WSL, Hyper-V) au lieu de sa véritable carte Wi-Fi.
* **Solution** :
  - Sur le PC 1, ouvrez PowerShell et tapez :
    ```powershell
    ipconfig
    ```
  - Parcourez la liste pour trouver la section intitulée **`Carte réseau sans fil Wi-Fi`** :
    ```text
    Carte réseau sans fil Wi-Fi :
       Adresse IPv4. . . . . . . . . . . . . .: 192.168.1.34
       Masque de sous-réseau . . . . . . . . .: 255.255.255.0
    ```
  - Vérifiez que le PC 2 possède une adresse débutant par les mêmes 3 chiffres (ex: `192.168.1.XX`).

---

### 1.5 Port TCP bloqué par le Pare-feu Windows Defender
* **Symptômes** : La connexion en boucle locale `127.0.0.1` fonctionne sur le même PC, mais échoue dès qu'on tente de connecter un second ordinateur distant.
* **Cause** : Par défaut, Windows Defender bloque les sockets d'écoute serveur sur les applications Python non signées.
* **Solution définitive** :
  Sur le **PC 1 (Hôte)**, ouvrez PowerShell en tant qu'Administrateur et exécutez la commande :
  ```powershell
  New-NetFirewallRule -DisplayName "Tank War TCP 4242" -Direction Inbound -LocalPort 4242 -Protocol TCP -Action Allow -Profile Private
  ```
  *(Cette commande autorise le trafic local sans affaiblir la sécurité de vos réseaux publics).*

---

### 1.6 Les deux PC ne sont pas sur le même réseau local
* **Symptômes** : Le PC 1 a une IP en `192.168.1.XX` et le PC 2 a une IP en `192.168.0.XX` ou `10.X.X.X`.
* **Causes Possibles** :
  - L'un des PC est connecté en Wi-Fi 2.4 GHz et l'autre sur un répéteur Wi-Fi créant un sous-réseau isolé.
  - L'un des PC est connecté en partage de connexion 4G et l'autre sur la box fixe.
* **Solution** :
  - Connectez impérativement les deux PC au **même nom de réseau Wi-Fi (SSID)**.
  - Vérifiez la connectivité avec un ping depuis le PC 2 vers le PC 1 :
    ```powershell
    ping 192.168.1.XX
    ```

---

### 1.7 Conflits causés par un logiciel VPN
* **Symptômes** : L'adresse IP détectée par le jeu est une adresse virtuelle (ex: `10.8.0.2` ou `100.64.X.X`) au lieu de l'IP du domicile.
* **Cause** : Les VPNs (NordVPN, ProtonVPN, OpenVPN, Cisco AnyConnect) détournent les tables de routage réseau.
* **Solution** :
  - Désactivez temporairement votre logiciel VPN sur les deux ordinateurs pendant vos parties en réseau local.

---

## 2. Déconnexions et Stabilité en Jeu

### 2.1 Déconnexion inattendue d'un joueur pendant la partie
* **Comportement du jeu** :
  - Si le Joueur 2 perd sa connexion (fermeture de l'application, mise en veille du PC, micro-coupure Wi-Fi) :
    - Le serveur autoritaire détecte immédiatement la rupture de flux socket.
    - Le char vert s'immobilise instantanément pour éviter qu'il n'avance indéfiniment.
    - Le serveur reste ouvert et prêt à accueillir une reconnexion immédiate.
* **Comment se reconnecter ?** :
  - Le Joueur 2 relance simplement son jeu sur le PC 2 et clique sur **`🔗 REJOINDRE UNE PARTIE`** pour réintégrer le match.

---

### 2.2 Problèmes de désynchronisation ou de saccades (Lag)
* **Causes Possibles** :
  - Signal Wi-Fi faible ou interférences avec d'autres appareils.
  - Nagle buffering actif (résolu dans notre code via `TCP_NODELAY`).
* **Solutions** :
  - Rapprochez les deux ordinateurs de la box Wi-Fi.
  - Si vous êtes loin d'une box, activez le **Point d'accès Wi-Fi mobile** sur votre smartphone posé entre les deux ordinateurs : le ping local passera sous la barre des $3\text{ ms}$ constants !

---

### 2.3 Le jeu se ferme brusquement (Crash)
* **Causes Possibles** :
  - Fermeture involontaire via la touche `Échap` (qui sert à quitter les menus ou afficher la pause).
  - Exception mémoire rare lors du redimensionnement de fenêtre.
* **Solution** :
  - Le jeu fonctionne en résolution fixe de $1600 \times 900$ pixels. Évitez de forcer le redimensionnement manuel de la bordure de fenêtre sous Windows.
  - Utilisez la touche `P` ou le bouton de pause de l'interface pour suspendre la partie en toute sécurité.

---

## 3. Problèmes Audiovisuels et Système

### 3.1 Aucun son ou mixer Pygame inactif
* **Causes Possibles** :
  - Périphérique de sortie audio débranché ou indisponible au moment du lancement.
  - Pilote audio désactivé.
* **Solution** :
  - Le module `SoundManager` intègre une protection *fail-safe* : si le sous-système audio Pygame ne s'initialise pas, le jeu continue de tourner parfaitement à 60 FPS sans planter.
  - Vérifiez dans Windows que votre casque ou vos haut-parleurs sont bien définis comme périphérique de sortie par défaut avant de lancer `main.py`.

---

### 3.2 Erreur d'installation de Pygame sous Python 3.14
* **Symptômes** : La commande `pip install pygame` échoue avec des erreurs de compilation C / SDL2 sous Python 3.14.
* **Cause** : La bibliothèque classique `pygame` ne fournit pas encore de roues pré-compilées (wheels) pour la toute récente version Python 3.14 sur Windows.
* **Solution** :
  - Notre fichier `requirements.txt` utilise **`pygame-ce`** (*Pygame Community Edition*, version 2.5.8+), qui propose des binaires officiels optimisés pour Python 3.12, 3.13 et 3.14 avec 100% de compatibilité API :
  ```powershell
  pip install -r requirements.txt
  ```

