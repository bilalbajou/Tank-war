"""Gestionnaire audio et générateur procédural d'effets sonores pour Tank War.

Génère des effets sonores 16-bit 44.1 kHz stéréo 100% originaux et libres de droits :
- Tir de canon (blast percutant avec transitoire)
- Explosion lourde de tank (onde de choc basse fréquence et réverbération)
- Collision métallique / impact d'obus
- Destruction de caisse en bois (craquement sec et éclatement)
- Collecte de bonus (carillon ascendant mélodieux)
- Fanfare de victoire (accord majeur triomphal)
- Son de défaite (accord mineur descendant)

Fournit un SoundManager avec gestion du volume global, activation/désactivation et pré-chargement.
"""

from __future__ import annotations
import math
import os
import struct
import wave
from pathlib import Path
from typing import Optional
import pygame

from settings import ASSETS_DIR

SOUNDS_DIR = ASSETS_DIR / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# SYNTHÉTISEUR AUDIO PROCÉDURAL (WAV 16-bit 44.1 kHz PCM)
# =============================================================================
def _write_wav_stereo(filename: Path, samples: list[float], sample_rate: int = 44100) -> None:
    """Écrit une liste d'échantillons normalisés [-1.0, 1.0] dans un fichier WAV stéréo."""
    with wave.open(str(filename), "wb") as wav_file:
        wav_file.setnchannels(2)  # Stéréo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        packed_data = bytearray()
        for s in samples:
            # Clamping [-1.0, 1.0]
            val = max(-1.0, min(1.0, s))
            int_val = int(val * 32767.0)
            frame = struct.pack("<hh", int_val, int_val)
            packed_data.extend(frame)

        wav_file.writeframes(packed_data)


def generate_all_sound_effects(force_regenerate: bool = False) -> None:
    """Génère tous les fichiers WAV du jeu s'ils ne sont pas déjà présents."""
    sample_rate = 44100

    # 1. Tir de canon (Shoot)
    shoot_path = SOUNDS_DIR / "shoot.wav"
    if force_regenerate or not shoot_path.exists():
        duration = 0.28
        total_samples = int(sample_rate * duration)
        samples = []
        seed = 42
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 22.0)
            # Fréquence glissante descendante (220 Hz -> 45 Hz)
            freq = 220.0 * math.exp(-t * 18.0) + 45.0
            sine = math.sin(2.0 * math.pi * freq * t)

            # Bruit blanc pseudo-aléatoire pour le souffle de la poudre
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            noise_env = math.exp(-t * 40.0)

            sample = (sine * 0.75 + noise * noise_env * 0.65) * env
            samples.append(sample)
        _write_wav_stereo(shoot_path, samples, sample_rate)

    # 2. Explosion de tank (Heavy Blast)
    explosion_path = SOUNDS_DIR / "explosion.wav"
    if force_regenerate or not explosion_path.exists():
        duration = 0.85
        total_samples = int(sample_rate * duration)
        samples = []
        seed = 1337
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 4.8)
            # Bass rumble (60 Hz -> 30 Hz)
            rumble_freq = 60.0 * math.exp(-t * 3.5) + 28.0
            sub_bass = math.sin(2.0 * math.pi * rumble_freq * t)

            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            # Crackle
            crackle = noise * math.sin(2.0 * math.pi * 120.0 * t)

            sample = (sub_bass * 0.6 + noise * 0.5 + crackle * 0.2) * env
            samples.append(sample)
        _write_wav_stereo(explosion_path, samples, sample_rate)

    # 3. Collision / Impact d'obus (Metal Thud)
    collision_path = SOUNDS_DIR / "collision.wav"
    if force_regenerate or not collision_path.exists():
        duration = 0.22
        total_samples = int(sample_rate * duration)
        samples = []
        seed = 999
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 26.0)
            ping = (
                math.sin(2.0 * math.pi * 520.0 * t) * 0.4
                + math.sin(2.0 * math.pi * 1040.0 * t) * 0.25
                + math.sin(2.0 * math.pi * 120.0 * t) * 0.5
            )
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            sample = (ping * 0.7 + noise * 0.3 * math.exp(-t * 50.0)) * env
            samples.append(sample)
        _write_wav_stereo(collision_path, samples, sample_rate)

    # 4. Destruction de caisse en bois (Wood Crack)
    crate_path = SOUNDS_DIR / "crate_break.wav"
    if force_regenerate or not crate_path.exists():
        duration = 0.32
        total_samples = int(sample_rate * duration)
        samples = []
        seed = 777
        for i in range(total_samples):
            t = i / sample_rate
            env = math.exp(-t * 14.0)
            wood_body = math.sin(2.0 * math.pi * 140.0 * t) * math.exp(-t * 18.0)

            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            # Craquements de lattes
            snap_freq = 600.0 + 300.0 * math.sin(t * 80.0)
            snap = math.sin(2.0 * math.pi * snap_freq * t) * noise

            sample = (wood_body * 0.65 + snap * 0.55) * env
            samples.append(sample)
        _write_wav_stereo(crate_path, samples, sample_rate)

    # 5. Collecte de bonus (Power-up Chime)
    powerup_path = SOUNDS_DIR / "powerup.wav"
    if force_regenerate or not powerup_path.exists():
        duration = 0.45
        total_samples = int(sample_rate * duration)
        samples = []
        # Arpège rapide montant : Do5 (523 Hz), Mi5 (659 Hz), Sol5 (784 Hz), Do6 (1046 Hz)
        notes = [523.25, 659.25, 783.99, 1046.50]
        note_dur = duration / len(notes)

        for i in range(total_samples):
            t = i / sample_rate
            note_idx = min(len(notes) - 1, int(t / note_dur))
            freq = notes[note_idx]
            local_t = t - (note_idx * note_dur)
            note_env = math.exp(-local_t * 9.0)

            # Sonnette cristalline avec harmonique 2 et 3
            sine = (
                math.sin(2.0 * math.pi * freq * t) * 0.65
                + math.sin(2.0 * math.pi * (freq * 2.0) * t) * 0.25
                + math.sin(2.0 * math.pi * (freq * 3.0) * t) * 0.1
            )
            samples.append(sine * note_env * 0.8)
        _write_wav_stereo(powerup_path, samples, sample_rate)

    # 6. Fanfare de victoire (Victory Major Fanfare)
    victory_path = SOUNDS_DIR / "victory.wav"
    if force_regenerate or not victory_path.exists():
        duration = 1.3
        total_samples = int(sample_rate * duration)
        samples = []
        # Séquence triomphale : Sol4 (392 Hz), Do5 (523 Hz), Mi5 (659 Hz), Sol5 (784 Hz long)
        steps = [
            (0.00, 0.20, 392.0),
            (0.20, 0.40, 523.25),
            (0.40, 0.60, 659.25),
            (0.60, 1.30, 783.99),
        ]
        for i in range(total_samples):
            t = i / sample_rate
            sample_val = 0.0
            for start, end, freq in steps:
                if start <= t < end:
                    lt = t - start
                    env = math.sin((lt / (end - start)) * math.pi * 0.5) if lt < 0.05 else math.exp(-lt * 2.2)
                    # Harmoniques cuivrées
                    tone = (
                        math.sin(2.0 * math.pi * freq * t) * 0.6
                        + math.sin(2.0 * math.pi * (freq * 2) * t) * 0.25
                        + math.sin(2.0 * math.pi * (freq * 3) * t) * 0.15
                    )
                    sample_val = tone * env
                    break
            samples.append(sample_val * 0.85)
        _write_wav_stereo(victory_path, samples, sample_rate)

    # 7. Son de défaite (Defeat Minor Descent)
    defeat_path = SOUNDS_DIR / "defeat.wav"
    if force_regenerate or not defeat_path.exists():
        duration = 1.2
        total_samples = int(sample_rate * duration)
        samples = []
        # Séquence mineure : Sol4 (392 Hz), Mib4 (311 Hz), Do4 (261 Hz), Si3 (246 Hz)
        steps = [
            (0.00, 0.25, 392.0),
            (0.25, 0.50, 311.13),
            (0.50, 0.75, 261.63),
            (0.75, 1.20, 246.94),
        ]
        for i in range(total_samples):
            t = i / sample_rate
            sample_val = 0.0
            for start, end, freq in steps:
                if start <= t < end:
                    lt = t - start
                    env = math.exp(-lt * 2.8)
                    tone = math.sin(2.0 * math.pi * freq * t) * 0.65 + math.sin(2.0 * math.pi * (freq * 0.5) * t) * 0.35
                    sample_val = tone * env
                    break
            samples.append(sample_val * 0.8)
        _write_wav_stereo(defeat_path, samples, sample_rate)


# =============================================================================
# GESTIONNAIRE AUDIO (SOUND MANAGER)
# =============================================================================
class SoundManager:
    """Gestionnaire singleton de tous les effets sonores et de leur volume."""

    _instance: Optional[SoundManager] = None

    def __new__(cls) -> SoundManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.enabled = True
        self.master_volume = 0.75
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        # Génère les fichiers WAV s'ils sont manquants
        try:
            generate_all_sound_effects(force_regenerate=False)
        except Exception as e:
            print(f"[SoundManager] Avertissement génération sons : {e}")

        # Initialisation sécurisée du mixer Pygame
        self._init_mixer()
        self._preload_sounds()

    def _init_mixer(self) -> None:
        """Initialise le sous-système audio Pygame s'il ne l'est pas déjà."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            self.enabled = False

    def _preload_sounds(self) -> None:
        """Charge l'intégralité des fichiers audio en mémoire pour un accès instantané sans I/O disque."""
        if not self.enabled or not pygame.mixer.get_init():
            return

        sound_files = {
            "shoot": SOUNDS_DIR / "shoot.wav",
            "explosion": SOUNDS_DIR / "explosion.wav",
            "collision": SOUNDS_DIR / "collision.wav",
            "crate_break": SOUNDS_DIR / "crate_break.wav",
            "powerup": SOUNDS_DIR / "powerup.wav",
            "victory": SOUNDS_DIR / "victory.wav",
            "defeat": SOUNDS_DIR / "defeat.wav",
        }

        for name, path in sound_files.items():
            if path.exists():
                try:
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(self.master_volume)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[SoundManager] Erreur chargement {name} : {e}")

    def set_volume(self, volume: float) -> None:
        """Modifie le volume global de tous les effets sonores (de 0.0 à 1.0)."""
        self.master_volume = max(0.0, min(1.0, float(volume)))
        for snd in self.sounds.values():
            try:
                snd.set_volume(self.master_volume)
            except Exception:
                pass

    def toggle_mute(self) -> bool:
        """Active ou désactive la coupure du son. Retourne l'état actif."""
        self.enabled = not self.enabled
        return self.enabled

    def play(self, sound_name: str, volume_scale: float = 1.0) -> None:
        """Joue un son pré-chargé sans bloquer."""
        if not self.enabled or not pygame.mixer.get_init():
            return

        snd = self.sounds.get(sound_name)
        if snd:
            try:
                vol = max(0.0, min(1.0, self.master_volume * volume_scale))
                snd.set_volume(vol)
                snd.play()
            except Exception:
                pass

    # Raccourcis express
    def play_shoot(self) -> None:
        self.play("shoot", volume_scale=0.85)

    def play_explosion(self) -> None:
        self.play("explosion", volume_scale=1.0)

    def play_collision(self) -> None:
        self.play("collision", volume_scale=0.7)

    def play_crate_break(self) -> None:
        self.play("crate_break", volume_scale=0.9)

    def play_powerup(self) -> None:
        self.play("powerup", volume_scale=0.95)

    def play_victory(self) -> None:
        self.play("victory", volume_scale=1.0)

    def play_defeat(self) -> None:
        self.play("defeat", volume_scale=0.9)


# Instance globale partagée
sound_manager = SoundManager()

