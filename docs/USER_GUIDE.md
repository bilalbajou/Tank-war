# 🎮 Guide Utilisateur — TANK WAR (Arena Duel)

Bienvenue dans le guide officiel de **Tank War : Arena Duel** ! Ce document vous présente le fonctionnement du jeu, les commandes, les règles du combat, les bonus et les astuces tactiques.

---

## 1. 🎯 Concept et Objectifs du Jeu

**Tank War** est un jeu d'affrontement tactique en 2D vue du dessus (*Top-Down*). Deux chars blindés s'affrontent dans une arène désertique fermée parsemée d'obstacles stratégiques (barrières métalliques, caisses de ravitaillement destructibles, rochers et cactus).

### 🏆 Objectif Principal
- **Premier joueur à marquer 5 points** remporte la victoire !
- Chaque joueur dispose de **3 vies** par manche.
- Éliminer les 3 vies de l'adversaire vous rapporte **1 point** et réinitialise la position des deux chars.
- **Durée maximale de la partie** : **90 secondes**.
  - Si le chrono expire : le joueur avec le score le plus élevé l'emporte.
  - En cas d'égalité à $00:00$ : la **Mort Subite** s'enclenche ! Le prochain coup fatal désigne immédiatement le vainqueur.

---

## 2. ⌨️ Commandes et Contrôles du Jeu

Le jeu est entièrement conçu pour être utilisable au **clavier** et à la **souris**.

### 2.1 Navigation dans les Menus et Salons (Lobby)

| Action | Contrôle Clavier | Contrôle Souris |
| :--- | :--- | :--- |
| **Naviguer entre les boutons** | `Flèche Haut` / `Flèche Bas` ou `Z` / `S` | Survol direct (effet de relief animé) |
| **Valider / Cliquer** | `Entrée` ou `Espace` | Clic gauche |
| **Retour / Annuler** | `Échap` | Clic sur le bouton *Annuler / Retour* |
| **Saisie de texte (IP)** | Clavier alphanumérique, pavé numérique, `Retour Arrière` | Clic pour activer le champ |

---

### 2.2 Contrôles en Combat (Duel)

| Action | Joueur 1 (Tank Rouge) | Joueur 2 (Tank Vert - Local) | Joueur 2 (Client LAN) |
| :--- | :--- | :--- | :--- |
| **Avancer (Haut)** | `Z` (ou `W`) | `Flèche Haut` | `Flèche Haut` |
| **Reculer (Bas)** | `S` | `Flèche Bas` | `Flèche Bas` |
| **Tourner à Gauche** | `Q` (ou `A`) | `Flèche Gauche` | `Flèche Gauche` |
| **Tourner à Droite** | `D` | `Flèche Droite` | `Flèche Droite` |
| **Déplacement Diagonal** | Combinaison de 2 touches (ex: `Z`+`D`) | Combinaison de 2 flèches | Combinaison de 2 flèches |
| **Tir de Canon** | `ESPACE` | `ENTRÉE` (ou `Pavé Num Entrée`) | `ENTRÉE` ou `ESPACE` |
| **Mettre en Pause** | `Échap` ou `P` | `Échap` ou `P` | `Échap` ou `P` |
| **Réinitialiser la manche** | `R` (Hôte / Local) | — | — |
| **Afficher Hitboxes (Debug)** | `F1` | `F1` | `F1` |

---

## 3. 🕹️ Modes de Jeu

### Mode 1 : Duel Local (2 Joueurs sur le même ordinateur)
Idéal pour jouer rapidement avec un ami sur le même clavier.
1. Lancez le jeu : `python main.py`.
2. Cliquez sur **⚔️ JOUER (LOCAL)**.
3. Dans le salon, appuyez sur **✅ TOUS PRÊTS** (ou `ESPACE`).
4. Le combat commence immédiatement après le décompte !

### Mode 2 : Multijoueur Réseau Local (Wi-Fi LAN)
Permet d'affronter un adversaire sur deux ordinateurs portables ou fixes connectés à la même box Wi-Fi ou partage de connexion mobile.
- **PC 1** clique sur **📡 HÉBERGER UNE PARTIE** et communique son IP affichée.
- **PC 2** clique sur **🔗 REJOINDRE UNE PARTIE**, saisit l'adresse IP de l'hôte et valide.
- Les deux joueurs cliquent sur **✅ JE SUIS PRÊT** dans le salon pour lancer le match !
*(Voir le document complet [docs/NETWORK_GUIDE.md](NETWORK_GUIDE.md) pour le tutoriel pas-à-pas).*

---

## 4. 📊 Affichage Tête Haute (HUD)

En cours de match, un bandeau d'information supérieur translucide présente :
- **Section Gauche (Joueur 1 Rouge)** :
  - 3 cœurs / blindages représentant les vies restantes.
  - Jauge de recharge du canon (s'estompe pendant les $0.45\text{ s}$ de rechargement).
  - Badges des bonus actifs (icônes bouclier, vitesse, tir rapide avec durée restante).
- **Section Centrale** :
  - **Score en direct** (ex: `3 - 2`, objectif de 5 points).
  - **Chronomètre de match** (décompte de 90 secondes). Si la mort subite est active, un bandeau rouge alerte clignote.
- **Section Droite (Joueur 2 Vert)** :
  - 3 cœurs de vie, rechargement et bonus du second joueur.
- **Bandeau Inférieur** :
  - Statut de la connexion réseau (ex: `🟢 CONNECTÉ À L'HÔTE (192.168.1.45:4242)`).

---

## 5. ⚡ Les Power-Ups (Bonus au Sol)

Toutes les 12 secondes, un bonus apparaît aléatoirement sur l'un des 8 emplacements dégagés de l'arène :

| Bonus | Visuel | Effet en Jeu | Durée |
| :---: | :---: | :--- | :---: |
| **Bouclier Énergétique** | Icône bleue avec bulle sphérique | Forme un dôme protecteur translucide qui absorbe les obus ennemis. Vos PV ne diminuent pas tant qu'il est actif. | **8 secondes** |
| **Vitesse Accrue** | Éclair doré avec lueur jaune | Augmente la vitesse de déplacement de $+50\%$ ($330\text{ px/s}$ au lieu de $220\text{ px/s}$), idéal pour esquiver. | **8 secondes** |
| **Tir Rapide** | Obus rouge avec traînée de feu | Divise par deux le délai de rechargement du canon ($0.225\text{ s}$ au lieu de $0.45\text{ s}$), doublant la puissance de feu. | **8 secondes** |

---

## 6. 🗺️ Éléments de l'Arène et Tactiques

1. **Barrières Jaunes et Noires & Rochers** :
   - Indestructibles. Bloquent à la fois les chars et les obus.
   - Utilisez-les comme abris pour forcer l'adversaire à s'exposer.
2. **Caisses en Bois** :
   - Bloquent les déplacements des chars.
   - **Destructibles** : un tir de canon les fissure, puis les fait exploser, ouvrant de nouveaux couloirs d'attaque surprise.
3. **Plantes et Cactus** :
   - Éléments purement décoratifs. Ils ne bloquent ni les déplacements ni les tirs de canon.
4. **Glissement le long des Murs** :
   - Le moteur physique intègre le *wall-sliding* : si vous avancez en diagonale contre un mur, votre char glisse naturellement le long de la paroi sans se coincer.

---

## 7. ⏸️ Menu Pause et Écran de Fin de Match

- **Mettre en pause** : Appuyez sur `Échap` ou `P` en plein combat.
  - `▶️ REPRENDRE` : Repart instantanément au combat.
  - `🔄 RECOMMENCER` : Réinitialise le score et les caisses à zéro.
  - `🏠 RETOUR AU MENU` : Ferme la session proprement et retourne à l'accueil.
- **Écran de Victoire / Défaite** :
  - Proclame le vainqueur avec sa raison de triomphe (*"Premier à 5 points"*, *"Temps écoulé"*, etc.).
  - Appuyez sur `R` pour relancer immédiatement une revanche.
  - Appuyez sur `Échap` pour revenir au menu principal.

