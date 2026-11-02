# 🚀 Guide de Déploiement et de Publication — TANK WAR (Arena Duel)

Ce guide complet vous explique pas-à-pas comment compiler **Tank War**, créer un exécutable Windows autonome (`.exe`), générer un installateur professionnel et publier votre jeu sur les principales plateformes de distribution (**Itch.io**, **GitHub Releases** et **Steam**).

---

## 📑 Sommaire
1. [Étape 1 : Compilation en Exécutable Windows (.exe)](#1--compilation-en-exécutable-windows-exe)
2. [Étape 2 : Publication sur Itch.io (Recommandé pour jeux indépendants)](#2--publication-sur-itchio-plateforme-indie-recommandée)
3. [Étape 3 : Publication sur GitHub Releases](#3--publication-sur-github-releases)
4. [Étape 4 : Création d'un Installateur Windows (.exe) avec Inno Setup](#4--création-dun-installateur-windows-avec-inno-setup)
5. [Étape 5 : Publication sur Steam (Steamworks)](#5--publication-sur-steam-steamworks)
6. [Étape 6 : Gestion du Pare-feu et de Windows SmartScreen](#6--gestion-de-windows-smartscreen-et-du-pare-feu)

---

## 1. 🔨 Compilation en Exécutable Windows (.exe)

Pour que vos joueurs puissent lancer le jeu d'un simple double-clic **sans avoir besoin d'installer Python ni aucune bibliothèque**, nous utilisons **PyInstaller**.

### A. Méthode Automatique Clé en Main (Recommandé)
Un script de build automatisé est inclus à la racine du projet : [`build_game.py`](file:///d:/sideproject/Tank%20war/build_game.py).

Ouvrez un terminal PowerShell dans le dossier du projet et exécutez :
```powershell
.\.venv\Scripts\python.exe build_game.py
```

Ce script effectue automatiquement toutes les étapes suivantes :
1. Vérifie et installe `pyinstaller` si nécessaire.
2. Vérifie la présence de tous les assets et des 30 icônes PNG 32-bit.
3. Compile le binaire fenêtré `TankWar.exe` (sans fenêtre d'invite de commandes noire) avec [`TankWar.spec`](file:///d:/sideproject/Tank%20war/TankWar.spec).
4. Génère le dossier autonome `dist/TankWar/`.
5. Compresse le dossier en une archive prête à la distribution :  
   📦 **`dist/TankWar-v1.0.0-Windows.zip`**.

### B. Tester l'Exécutable Généré
Une fois la compilation terminée, vous pouvez tester directement votre jeu :
```powershell
.\dist\TankWar\TankWar.exe
```

---

## 2. 🎮 Publication sur Itch.io (Plateforme Indie Recommandée)

**Itch.io** est la plateforme la plus populaire et la plus accessible pour les jeux vidéo indépendants. Elle permet de distribuer votre jeu gratuitement ou avec paiement libre (*Pay what you want*), sans aucun frais d'entrée.

### A. Publication via l'Interface Web (En 5 minutes)
1. **Créer un compte** sur [itch.io](https://itch.io).
2. Rendez-vous sur votre tableau de bord et cliquez sur **« Create new project »**.
3. Remplissez les informations de base :
   - **Title** : `Tank War : Arena Duel`
   - **Classification** : `Games`
   - **Kind of project** : `Downloadable` (Fichiers téléchargeables)
   - **Release status** : `Released`
   - **Pricing** : `$0 or donate` (ou montant libre de votre choix)
4. **Téléverser le jeu** :
   - Dans la section **Uploads**, cliquez sur **Upload files**.
   - Sélectionnez votre archive zip : `dist/TankWar-v1.0.0-Windows.zip`.
   - Cochez la case **`Executable`** et l'icône **`Windows`**.
5. **Personnaliser la page** :
   - Ajoutez des captures d'écran de l'arène de combat et du menu.
   - Rédigez une brève description du gameplay (duel 2 joueurs LAN Wi-Fi sans Internet, mode solo contre IA).
   - Indiquez les contrôles (`ZQSD` / `Flèches` / `Espace`).
6. Cliquez sur **Save & View Page**, puis passez la visibilité sur **« Public »** !

### B. Déploiement Continu avec Butler CLI (Pour mises à jour automatiques)
Itch.io propose son propre outil en ligne de commande, **Butler**, permettant de déployer de nouvelles versions en quelques secondes par calcul de delta :
1. Téléchargez Butler : [itch.io/docs/butler](https://itch.io/docs/butler).
2. Connectez-vous : `butler login`.
3. Poussez votre build :
   ```bash
   butler push dist/TankWar votre-pseudo/tank-war:windows
   ```

---

## 3. 🌐 Publication sur GitHub Releases

Idéal pour votre portfolio, vos collaborateurs ou la communauté open-source.

### A. Déploiement Automatisé par GitHub Actions
Le projet inclut déjà le workflow [`.github/workflows/build_and_publish.yml`](file:///d:/sideproject/Tank%20war/.github/workflows/build_and_publish.yml).

Dès que vous poussez un tag de version sur GitHub :
```bash
git tag v1.0.0
git push origin v1.0.0
```
Le serveur GitHub Actions Windows :
1. Installe les dépendances et exécute les 100 tests automatisés avec `pytest`.
2. Compile l'exécutable avec `build_game.py`.
3. Crée automatiquement une **Release** sur votre dépôt GitHub avec le fichier `TankWar-v1.0.0-Windows.zip` en téléchargement direct !

### B. Téléversement Manuel
1. Rendez-vous sur votre dépôt GitHub : `https://github.com/votre-compte/tank-war/releases`.
2. Cliquez sur **Draft a new release**.
3. Choisissez une étiquette (ex: `v1.0.0`), donnez un titre et glissez-déposez `dist/TankWar-v1.0.0-Windows.zip`.
4. Cliquez sur **Publish release**.

---

## 4. 📦 Création d'un Installateur Windows avec Inno Setup

Pour offrir une expérience professionnelle avec raccourci sur le Bureau et désinstallateur propre dans le Panneau de configuration Windows :

1. Téléchargez et installez **Inno Setup** (gratuit et open-source) : [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php).
2. Le fichier de configuration prêt à l'emploi [`installer.iss`](file:///d:/sideproject/Tank%20war/installer.iss) est déjà présent à la racine du projet.
3. Ouvrez `installer.iss` dans Inno Setup Compiler et cliquez sur **Build > Compile** (ou `Ctrl + F9`).
4. Inno Setup génère instantanément :  
   💿 **`dist/TankWar_Setup_v1.0.0.exe`**.

Vos joueurs n'ont plus qu'à lancer cet installateur pour installer le jeu dans `C:\Program Files\TankWar` avec un raccourci sur leur bureau.

---

## 5. 🚢 Publication sur Steam (Steamworks)

Si vous souhaitez commercialiser ou distribuer le jeu sur **Steam** :

1. **Compte Développeur Steamworks** :
   - Inscrivez-vous sur [partner.steamgames.com](https://partner.steamgames.com) et réglez les frais Steam Direct ($100 par jeu).
2. **Configuration du Dépôt SteamPipe** :
   - Téléchargez l'outil **SteamPipe SDK**.
   - Pointez le dépôt Windows vers le contenu du dossier `dist/TankWar/`.
   - Définissez l'exécutable de lancement : `TankWar.exe`.
3. **Steam Cloud & Succès (Optionnel)** :
   - Vous pouvez intégrer la bibliothèque Python `steamworks-py` si vous souhaitez ajouter des succès Steam ou le temps de jeu.
4. **Vérification & Lancement** :
   - Soumettez la page du magasin et le build aux équipes de Valve pour validation (délai de 3 à 5 jours ouvrés).

---

## 6. 🛡️ Gestion de Windows SmartScreen et du Pare-feu

### A. L'avertissement Windows SmartScreen (« Application inconnue »)
Lorsqu'un joueur télécharge un exécutable indépendant récent sur Internet, Windows Defender affiche souvent :
> *"Windows a protégé votre ordinateur. Microsoft Defender SmartScreen a empêché le démarrage d'une application non reconnue."*

- **Pourquoi ?** Microsoft exige un certificat de signature de code payant (environ 200 à 400 € / an) pour attribuer une réputation immédiate.
- **Que doivent faire vos joueurs ?**  
  Il suffit de cliquer sur **« Informations complémentaires »** puis **« Exécuter quand même »**. Ce comportement est standard pour tous les jeux indépendants gratuits sur Itch.io.
- **Mention sur votre page de téléchargement** :  
  Ajoutez une note rassurante sur votre page Itch.io / GitHub :  
  *« Si Windows SmartScreen s'affiche au premier lancement, cliquez sur "Informations complémentaires" puis "Exécuter quand même". Le code est open-source et vérifié. »*

### B. Autorisation du Pare-feu pour le Multijoueur LAN
Puisque le jeu héberge un serveur TCP sur le port `4242` et utilise le broadcast UDP `4245` pour la détection Zero-Config :
- Lors du tout premier lancement en mode Hôte, Windows affichera une boîte de dialogue demandant d'autoriser `TankWar.exe` sur les réseaux privés.
- Le joueur doit simplement cocher **« Réseaux privés (domestiques) »** et cliquer sur **« Autoriser l'accès »**.

