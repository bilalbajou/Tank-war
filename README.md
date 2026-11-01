# 🛡️ Tank War : Arena Duel

**Tank War : Arena Duel** est un jeu vidéo de combat de tanks en 2D, vue du dessus (*Top-Down*), conçu pour 2 joueurs s'affrontant en réseau local (LAN Wi-Fi) sans aucune dépendance à Internet.

Deux tanks s'affrontent dans une arène désertique fermée parsemée d'obstacles stratégiques (barrières rocheuses, caisses de ravitaillement destructibles, buissons végétaux).

---

## 📐 Spécifications et Technologies

| Caractéristique | Spécification |
| :--- | :--- |
| **Langage** | Python 3.12+ (testé et compatible 3.14) |
| **Moteur Graphique** | Pygame / Pygame-ce 2.5+ |
| **Architecture Réseau** | Sockets TCP client/serveur avec framing binaire |
| **Sérialisation** | JSON standardisé |
| **Concurrence** | Multithreading (Threads non-bloquants I/O réseau) |
| **Résolution de référence** | 1600 × 900 (Format 16:9 fixe) |
| **Fréquence de rafraîchissement** | 60 FPS constants avec delta-time |
| **Suite de tests** | Pytest 8.0+ (80 tests unitaires & d'intégration) |

---

## 📚 Guides et Documentation Détaillée

Pour explorer chaque dimension du projet en profondeur, consultez les documents techniques dédiés dans le dossier `docs/` :

| Document | Description |
| :--- | :--- |
| 📖 [**docs/PROJECT_DOCUMENTATION.md**](docs/PROJECT_DOCUMENTATION.md) | **Architecture Technique Complète** : Principes SOLID, diagrammes d'architecture et de flux, classes métier (`Tank`, `CollisionHandler`, `MatchState`), CCD anti-tunneling, moteur balistique, audio et pipeline d'actifs. |
| 🌐 [**docs/NETWORK_GUIDE.md**](docs/NETWORK_GUIDE.md) | **Guide Réseau LAN Wi-Fi (Tutoriel Pas-à-Pas)** : Connexion 2 PC sans Internet, commandes PowerShell pour Pare-feu Windows, contournement de l'isolation AP, protocole TCP JSON à 30 Hz et diagrammes de séquence. |
| 🎮 [**docs/USER_GUIDE.md**](docs/USER_GUIDE.md) | **Guide du Joueur & Commandes** : Règles des matchs, contrôles clavier/souris, power-ups (Bouclier, Vitesse, Tir Rapide), tactiques d'arène et gestion des manches. |
| ❓ [**docs/FAQ.md**](docs/FAQ.md) | **Dépannage & FAQ Technique** : Résolution des erreurs *Connection Refused*, *Connection Timeout*, déconnexions brutales, sous-réseaux, VPN et audio. |

---

## 🏛️ Architecture Logicielle Modulaire & Principes SOLID

Le projet applique une séparation stricte des responsabilités (inspirée de Clean Architecture et MVC) :

```
                        +----------------------------+
                        |         GameEngine         |
                        | (Cycle de vie & 60 FPS)    |
                        +--------------+-------------+
                                       |
        +------------------+-----------+-----------+-------------------+
        |                  |                       |                   |
        v                  v                       v                   v
+---------------+  +---------------+       +---------------+   +---------------+
|     Input     |  |     State     |       |     Game      |   |   Rendering   |
| (InputHandler)|  | (StateManager)|       | (Pure Domain) |   |  (Renderer &  |
| Keyboard->Cmd |  |  Menu/Lobby/  |       | Arena, Tanks, |   | AssetManager) |
+-------+-------+  |    Playing    |       |  Collisions   |   +-------+-------+
        |          +---------------+       +-------+-------+           |
        |                                          ^                   |
        |                                          |                   |
        +------------------------------------------+                   |
        |            (Commandes neutres)                               |
        v                                                              v
+---------------+                                              +---------------+
|    Network    |                                              | Pygame Window |
| (TCP / JSON)  |<============================================>|  1600 x 900   |
+---------------+                                              +---------------+
```

### Application des principes SOLID :
1. **S - Single Responsibility Principle (SRP)** :
   - `src/game/` : Logique pure du monde, des tanks et des projectiles, totalement découplée de Pygame (simulation exécutable en mode headless sur le serveur).
   - `src/rendering/` : Affichage uniquement, ne mute aucun état métier.
   - `src/input/` : Traduit les événements matériels en objets `PlayerCommand` neutres.
   - `src/network/` : Gère le transport TCP, l'encodage binaire/JSON et les threads de flux sans connaître l'écran ni les touches.
2. **O - Open/Closed Principle (OCP)** :
   - Les entités dérivent de la classe de base `Entity`. L'ajout de nouveaux types d'obstacles ou de bonus s'effectue sans modifier le moteur de collision ni la boucle de rendu.
3. **L - Liskov Substitution Principle (LSP)** :
   - Toutes les entités (`Tank`, `Projectile`, `Obstacle`) respectent le contrat d'interface `Entity` (`position`, `bounding_box`, `update`).
4. **I - Interface Segregation Principle (ISP)** :
   - Les commandes d'action sont indépendantes de la socket de transport, permettant de tester le gameplay localement sans réseau.
5. **D - Dependency Inversion Principle (DIP)** :
   - Le moteur central orchestre des abstractions et reçoit ses dépendances via le module de configuration (`GameConfig`).

---

## 📂 Arborescence du Projet

```text
Tank war/
├── .gitignore                     # Fichiers exclus du versionnement
├── requirements.txt               # Dépendances Python (pygame-ce, pytest)
├── README.md                      # Documentation du projet
├── settings.py                    # Constantes globales, dimensions et palette de couleurs
├── generate_assets.py             # Script de génération des sprites PNG cartoon
├── main.py                        # Visualisateur de l'arène 2D avec débogage des collisions
│
├── assets/                        # Ressources multimédias
│   ├── maps/                      # Textures de la carte (desert_background.png, border_tile.png)
│   ├── obstacles/                 # Sprites PNG transparents (crates, barriers, rocks, plants)
│   ├── sounds/                    # Effets sonores
│   └── fonts/                     # Typographies TTF
│
├── docs/                          # Documentation technique et guides utilisateurs
│   ├── PROJECT_DOCUMENTATION.md   # Architecture technique complète, classes, CCD, SOLID
│   ├── NETWORK_GUIDE.md           # Tutoriel pas-à-pas multijoueur LAN Wi-Fi sans Internet
│   ├── USER_GUIDE.md              # Guide utilisateur, commandes, power-ups, tactiques
│   └── FAQ.md                     # Dépannage réseau, pare-feu, timeout, crash, audio
│
├── game/                          # Logique de jeu, carte et balistique
│   ├── __init__.py
│   ├── asset_manager.py           # Cache mémoire des surfaces pré-pivotées et textures
│   ├── collision.py               # Résolution continue des collisions (CCD anti-tunneling)
│   ├── effects.py                 # Particules, explosions, étincelles et animations
│   ├── game_state.py              # Arbitre de match (3 vies, score à 5, chrono 90s, mort subite)
│   ├── map.py                     # ArenaMap (décor, bordures, obstacles et caisses)
│   ├── obstacle.py                # Classes Obstacle, Decoration et Debris
│   ├── powerup.py                 # PowerUp et PowerUpManager (Bouclier, Vitesse, Tir Rapide)
│   ├── projectile.py              # Obus balistique orienté
│   ├── projectile_manager.py      # Gestion des tirs, étincelles et impacts
│   └── sound_manager.py           # Synthèse procédurale WAV et mixage audio
│
├── interface/                     # Interface utilisateur complète (Cartoon 2D)
│   ├── __init__.py
│   ├── components.py              # Composants réutilisables (UIButton, UITextInput, UIPanel)
│   ├── menu.py                    # Menu Principal (Logo, Jouer, Héberger, Rejoindre, Quitter)
│   ├── lobby.py                   # Salon d'attente (Fiches joueurs, statut Prêt, compte à rebours)
│   ├── screens.py                 # Écrans Héberger (IP/Port), Rejoindre (Saisie IP), Pause, Fin de Match
│   ├── hud.py                     # Affichage têtes-hautes (vies, score, timer, powerups)
│   └── scoreboard.py              # Écran de fin de match et bandeau de mort subite
│
├── network/                       # Couche réseau multijoueur TCP autoritaire
│   ├── __init__.py
│   ├── connection.py              # Sockets TCP avec TCP_NODELAY, thread I/O et framing \n
│   ├── protocol.py                # Protocole JSON, commandes d'entrées, lobby et instantanés
│   ├── server.py                  # Serveur TCP autoritaire (30 Hz, détection IP LAN)
│   └── client.py                  # Client TCP non-bloquant
│
├── players/                       # Entités de chars et contrôleurs
│   ├── __init__.py
│   ├── tank.py                    # Classe Tank (rotation, vitesse, vie, hitbox, draw, move)
│   └── controls.py                # Contrôleurs clavier distincts (P1 ZQSD, P2 Flèches)
│
├── src/                           # Architecture modulaire (Moteur, Réseau, Input)
│   ├── core/                      # Moteur, boucle et configuration
│   ├── game/                      # Logique métier pure (indépendante de Pygame)
│   ├── input/                     # Contrôleur d'entrées
│   ├── rendering/                 # Vue et affichage Pygame
│   ├── network/                   # Couche réseau TCP
│   └── ui/                        # Menus et composants d'interface
│
└── tests/                         # Suite de 75 tests automatisés Pytest
    ├── test_audio_visuals.py      # Tests AssetManager, SoundManager et EffectsManager
    ├── test_collisions_advanced.py# Anti-tunneling (CCD), destruction caisses, débris
    ├── test_combat.py             # Tests balistiques, cooldown, tir canon et dégâts
    ├── test_config.py             # Validation des constantes
    ├── test_map.py                # Tests des collisions, bordures, spawns et décors
    ├── test_models.py             # Tests du domaine (Vector2D, collisions, commandes)
    ├── test_network.py            # Handshake, framing \n, diffusion 30 Hz, reconnexion, déconnexion
    ├── test_progression.py        # Règles, 3 vies, score à 5, chrono 90s, mort subite, bonus
    ├── test_protocol.py           # Tests du protocole réseau et du framing
    ├── test_tank.py               # Tests 8 directions, vitesse dt, rotation et collisions tanks
    └── test_ui_screens.py         # Boutons, saisie IP, menu, lobby, pause, fin de partie, transitions
```

---

## 🎮 Commandes de Jeu

### Navigation dans les Menus et Salons (Lobby)
- **Souris** : Survol interactif avec effet d'élévation, clic gauche pour activer / valider.
- **Clavier** : `Flèche Haut` / `Flèche Bas` ou `Z` / `S` pour naviguer entre les boutons.
- **Validation** : `Entrée` ou `Espace`.
- **Retour / Annulation** : `Échap`.
- **En jeu** : `Échap` ou `P` pour ouvrir le menu Pause.

### Contrôles en Combat (Duel)

| Action | Joueur 1 (Tank Rouge) | Joueur 2 (Tank Vert) |
| :--- | :--- | :--- |
| **Avancer (Haut)** | `Z` (ou `W`) | `Flèche Haut` |
| **Reculer (Bas)** | `S` | `Flèche Bas` |
| **Gauche** | `Q` (ou `A`) | `Flèche Gauche` |
| **Droite** | `D` | `Flèche Droite` |
| **Déplacement Diagonal** | Combinaison de 2 touches (ex: `Z`+`D`) | Combinaison de 2 flèches |
| **Tir de Projectile (Canon)** | `ESPACE` | `ENTRÉE` |
| **Réinitialiser le match** | `R` | `R` |
| **Menu Pause** | `Échap` ou `P` | `Échap` ou `P` |
| **Mode Debug Hitboxes** | `F1` | `F1` |
| **Quitter** | `Échap` | `Échap` |

---

## 🚀 Installation et Lancement

### 1. Prérequis
- Python 3.12 ou supérieur installé.

### 2. Configuration de l'environnement virtuel
```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Sur Windows (PowerShell) :
.\.venv\Scripts\Activate.ps1
# Sur Linux / macOS :
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Exécution du jeu

#### A. Mode Multijoueur Réseau Local Wi-Fi (LAN sans Internet)
Ce mode permet d'affronter un adversaire sur deux ordinateurs distincts connectés à la même box ou point d'accès Wi-Fi :

1. **Sur le PC 1 (Serveur Hôte + Joueur 1 Rouge)** :
   ```bash
   python main.py --host
   ```
   *L'application affiche l'adresse IP locale à communiquer à votre adversaire (ex: `192.168.1.45:4242`).*

2. **Sur le PC 2 (Client distant + Joueur 2 Vert)** :
   ```bash
   python main.py --join 192.168.1.45
   ```
   *Le client se connecte instantanément, envoie ses commandes de touches et reçoit l'état officiel à 30 Hz.*

#### B. Mode Local (2 joueurs sur le même ordinateur)
```bash
python main.py --local
```
*Joueur 1 contrôle le tank rouge avec ZQSD + ESPACE, Joueur 2 contrôle le tank vert avec les FLÈCHES + ENTRÉE.*

### 4. Architecture Réseau TCP & Protocole
- **Modèle Serveur Autoritaire** : Le PC 1 calcule la physique continue, les collisions CCD, la balistique, les dégâts et les scores. Le client ne peut pas tricher ni décréter un coup.
- **Transport TCP & Framing** : Paquets JSON délimités par `\n` avec option `TCP_NODELAY` activée pour éliminer toute latence de buffering de Nagle.
- **Fréquence de Synchronisation** : 30 instantanés par seconde (30 Hz) vers le client, simulation locale à 60 FPS constants.
- **Régulation de Tir & Limite Joueurs** : Cooldowns de tir validés côté serveur, limitation stricte à 2 joueurs (refus automatique de tiers).

---

## 🌐 Configuration du Réseau Wi-Fi Local (LAN)

Le jeu fonctionne intégralement **sans connexion à Internet**. Deux configurations réseau typiques sont possibles :

### Option 1 : Via votre Box Internet / Routeur Wi-Fi
1. Connectez le **PC 1** et le **PC 2** au même réseau Wi-Fi domestique.
2. Assurez-vous que le réseau n'est pas configuré en mode « Wi-Fi Invité » (le mode invité isole les machines entre elles et bloque la communication locale).

### Option 2 : Sans Box / En déplacement (Point d'accès mobile)
1. Activez le **Partage de connexion (Point d'accès Wi-Fi)** sur un smartphone ou depuis l'un des deux PC sous Windows (Paramètres > Réseau > Point d'accès sans fil mobile).
2. Connectez les deux ordinateurs à ce point d'accès. Aucune consommation de données mobiles 4G/5G n'aura lieu puisque les données transitent exclusivement en local.

---

## 🛠️ Guide de Résolution des Erreurs Fréquentes

### 1. « Impossible de joindre l'hôte » / « Délai d'attente dépassé »
* **Cause 1 : Pare-feu Windows Defender bloquant le port 4242**  
  Windows bloque parfois les sockets entrantes non déclarées.  
  *Solution :* Ouvrez PowerShell en tant qu'administrateur sur le PC 1 et autorisez le port :
  ```powershell
  New-NetFirewallRule -DisplayName "TankWar TCP 4242" -Direction Inbound -LocalPort 4242 -Protocol TCP -Action Allow
  ```
* **Cause 2 : Mauvaise adresse IP saisie**  
  Vérifiez l'adresse IP locale exacte de l'hôte en tapant dans PowerShell :
  ```powershell
  ipconfig
  ```
  *(Recherchez la ligne « Adresse IPv4 » sur la carte sans fil Wi-Fi, ex: 192.168.1.XX).*
* **Cause 3 : VPN actif**  
  Certains VPNs (NordVPN, Proton, OpenVPN) créent des tunnels virtuels qui masquent l'adaptateur Wi-Fi local. Désactivez temporairement votre VPN.

### 2. « Port 4242 déjà utilisé » (Address already in use)
* **Cause :** Une instance précédente du serveur est encore active en arrière-plan.  
* **Solution :** Changez simplement de port lors du lancement :
  ```bash
  # Sur le PC 1 :
  python main.py --host --port 4243
  # Sur le PC 2 :
  python main.py --join 192.168.1.XX:4243
  ```

### 3. Le Joueur 2 est déconnecté brusquement
* Le serveur autoritaire détecte instantanément la rupture de socket, immobilise le char vert et se remet automatiquement en attente de reconnexion.  
* Le Joueur 2 peut relancer sa commande `--join <IP>` à tout moment pour reprendre le combat sans redémarrer le serveur.

---

## 🧪 Suite de Tests Automatisés

Le projet comprend **75 tests automatisés** couvrant l'intégralité du cycle de vie du jeu (physique CCD, balistique, synchronisation réseau TCP, déconnexions/reconnexions, cycle d'arbitrage et composants d'interface).

Pour exécuter la suite complète de tests :
```powershell
.\.venv\Scripts\pytest.exe -v
```

Tous les modules sont vérifiés et garantissent un taux de réussite de **100% (75/75)**.

---

## 🎨 Mécanisme de Repli Graphique (Fallback Procédural)
Le module `AssetManager` intègre un système de fallback intelligent :
- Si les fichiers PNG ne sont pas encore présents dans le dossier `assets/sprites/`, le jeu génère automatiquement des formes vectorielles stylisées (châssis orienté, tourelle, canon, caisses en bois avec croix, buissons).
- Dès qu'un sprite PNG est ajouté dans le répertoire dédié, il est automatiquement pris en charge sans modifier une seule ligne de code.

