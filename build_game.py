"""Script d'automatisation de packaging et de build pour Tank War (Arena Duel).

Fonctionnalités :
1. Vérification de l'environnement et installation automatique de PyInstaller.
2. Vérification et régénération éventuelle des assets et des icônes 32-bit.
3. Compilation en exécutable Windows (.exe) autonome avec TankWar.spec.
4. Création d'une archive ZIP prête pour distribution (Itch.io, GitHub Releases).
"""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Configuration de l'encodage de sortie pour compatibilité console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
ASSETS_DIR = BASE_DIR / "assets"


def run_cmd(cmd: list[str], desc: str) -> bool:
    """Exécute une commande système avec journalisation claire."""
    print(f"\n[BUILD] ... {desc}...")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"[ERREUR] Échec de l'étape : {desc} (Code {result.returncode})")
        return False
    print(f"[BUILD] [OK] {desc} terminé avec succès.")
    return True


def ensure_dependencies() -> bool:
    """Installe PyInstaller et Pillow dans l'environnement virtuel si absent."""
    ok = True
    try:
        import PyInstaller
        print(f"[BUILD] PyInstaller détecté (version {PyInstaller.__version__}).")
    except ImportError:
        print("[BUILD] PyInstaller non trouvé. Installation automatique via pip...")
        ok = run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"], "Installation de PyInstaller") and ok

    try:
        import PIL
    except ImportError:
        print("[BUILD] Pillow non trouvé. Installation automatique via pip...")
        ok = run_cmd([sys.executable, "-m", "pip", "install", "pillow"], "Installation de Pillow") and ok

    return ok


def ensure_app_ico() -> None:
    """Génère l'icône Windows multi-résolution app.ico si absente."""
    ico_path = ASSETS_DIR / "icons" / "app.ico"
    if ico_path.exists():
        return
    tank_img = ASSETS_DIR / "tanks" / "tank_green.png"
    if not tank_img.exists():
        return
    try:
        from PIL import Image
        tank = Image.open(tank_img).convert("RGBA")
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        ratio = min(210 / tank.width, 210 / tank.height)
        new_w = int(tank.width * ratio)
        new_h = int(tank.height * ratio)
        resized = tank.resize((new_w, new_h), Image.Resampling.LANCZOS)
        pos = ((256 - new_w) // 2, (256 - new_h) // 2)
        canvas.paste(resized, pos, resized)
        ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        canvas.save(ico_path, format="ICO", sizes=ico_sizes)
        print("[BUILD] [OK] assets/icons/app.ico généré avec succès.")
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible de générer app.ico: {e}")


def verify_assets() -> bool:
    """Vérifie la présence des ressources ou déclenche leur génération."""
    icons_dir = ASSETS_DIR / "icons"
    if not icons_dir.exists() or len(list(icons_dir.rglob("*.png"))) < 20:
        print("[BUILD] Génération des 30 icônes PNG d'interface...")
        if not run_cmd([sys.executable, "generate_icons.py"], "Génération des icônes"):
            return False

    sprites_dir = ASSETS_DIR / "tanks"
    if not sprites_dir.exists():
        print("[BUILD] Génération des sprites d'arène...")
        if not run_cmd([sys.executable, "generate_assets.py"], "Génération des sprites"):
            return False

    ensure_app_ico()
    return True


def compile_executable() -> bool:
    """Exécute PyInstaller avec TankWar.spec."""
    spec_file = BASE_DIR / "TankWar.spec"
    if not spec_file.exists():
        print("[ERREUR] Fichier TankWar.spec introuvable.")
        return False

    return run_cmd([sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_file)], "Compilation de TankWar.exe")


def create_release_zip(version: str = "1.0.0") -> Path:
    """Crée une archive ZIP prête pour Itch.io / GitHub Releases."""
    target_folder = DIST_DIR / "TankWar"
    zip_path = DIST_DIR / f"TankWar-v{version}-Windows.zip"

    print(f"\n[BUILD] Creation de l'archive de déploiement : {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(target_folder):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(target_folder)
                zf.write(file_path, arcname=str(Path("TankWar") / rel_path))

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[BUILD] [OK] Archive générée avec succès : {zip_path.name} ({zip_size_mb:.2f} Mo)")
    return zip_path


def main() -> int:
    """Point d'entrée principal du build."""
    print("=" * 65)
    print("PIPELINE DE DÉPLOIEMENT TANK WAR : ARENA DUEL")
    print("=" * 65)

    if not ensure_dependencies():
        return 1

    if not verify_assets():
        return 1

    if not compile_executable():
        return 1

    zip_file = create_release_zip("1.0.0")

    print("\n" + "=" * 65)
    print("DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !")
    print("=" * 65)
    print(f"Dossier du jeu : {DIST_DIR / 'TankWar'}")
    print(f"Archive ZIP    : {zip_file}")
    print("\nVous pouvez maintenant :")
    print("  1. Tester directement l'exécutable : .\\dist\\TankWar\\TankWar.exe")
    print("  2. Uploader l'archive ZIP sur Itch.io (https://itch.io/game/new)")
    print("  3. Publier la release sur GitHub (Releases > New Release)")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
