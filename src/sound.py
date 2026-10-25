"""
MarketQuest - Sound Effects & Audio Manager
Generates 8-bit procedural retro chimes and sound effects using raw PCM buffers.
Works without external audio files, with graceful silence fallbacks.
"""

import math
import struct
import pygame
from typing import Optional, Dict

class SoundManager:
    _instance: Optional['SoundManager'] = None

    def __init__(self, sfx_volume: float = 0.7):
        self.enabled = False
        self.sfx_volume = sfx_volume
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        if pygame.mixer and pygame.mixer.get_init():
            self.enabled = True
            self._generate_procedural_sounds()

    @classmethod
    def get_instance(cls) -> 'SoundManager':
        if cls._instance is None:
            cls._instance = SoundManager()
        return cls._instance

    def _generate_tone(self, freq_start: float, freq_end: float, duration: float, 
                       wave_type: str = 'square', decay: float = 3.0) -> Optional[pygame.mixer.Sound]:
        """Generate a procedural 8-bit retro sound using 16-bit PCM buffer matching mixer config."""
        if not self.enabled:
            return None
        try:
            init = pygame.mixer.get_init()
            if not init:
                return None
            sample_rate, _, channels = init
            total_samples = int(sample_rate * duration)
            buf = bytearray()

            for i in range(total_samples):
                t = i / total_samples
                # Exponential / linear envelope decay
                env = math.exp(-decay * t)
                # Frequency sweep
                freq = freq_start + (freq_end - freq_start) * t
                phase = 2.0 * math.pi * freq * (i / sample_rate)

                if wave_type == 'square':
                    val = 0.35 if (math.sin(phase) > 0) else -0.35
                elif wave_type == 'triangle':
                    val = 0.5 * (2.0 / math.pi) * math.asin(math.sin(phase))
                elif wave_type == 'noise':
                    import random
                    val = 0.25 * (random.random() * 2.0 - 1.0)
                else:  # sine
                    val = 0.5 * math.sin(phase)

                sample_int = int(32767.0 * val * env)
                sample_int = max(-32768, min(32767, sample_int))
                sample_bytes = struct.pack('<h', sample_int)

                # Duplicate for stereo if mixer has 2 channels
                for _ in range(channels):
                    buf += sample_bytes

            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _generate_chord(self, freqs: list[float], duration: float) -> Optional[pygame.mixer.Sound]:
        """Generate a multi-note arpeggio / chord."""
        if not self.enabled:
            return None
        try:
            init = pygame.mixer.get_init()
            if not init:
                return None
            sample_rate, _, channels = init
            note_dur = duration / len(freqs)
            buf = bytearray()

            for note_idx, freq in enumerate(freqs):
                sub_samples = int(sample_rate * note_dur)
                for i in range(sub_samples):
                    t = i / sub_samples
                    env = math.exp(-2.5 * t)
                    phase = 2.0 * math.pi * freq * (i / sample_rate)
                    val = 0.35 if math.sin(phase) > 0 else -0.35
                    sample_int = int(32767.0 * val * env)
                    sample_int = max(-32768, min(32767, sample_int))
                    b = struct.pack('<h', sample_int)
                    for _ in range(channels):
                        buf += b

            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    def _generate_procedural_sounds(self):
        # 1. Click: subtle short tick
        s_click = self._generate_tone(600, 400, 0.04, wave_type='triangle', decay=15.0)
        if s_click: self.sounds['click'] = s_click

        # 2. Buy: bright two-tone cash register chime (C6 -> G6)
        s_buy = self._generate_chord([1046.5, 1567.98], 0.16)
        if s_buy: self.sounds['buy'] = s_buy

        # 3. Sell: upbeat coin chime (E6 -> B6)
        s_sell = self._generate_chord([1318.5, 1975.5], 0.18)
        if s_sell: self.sounds['sell'] = s_sell

        # 4. Error: low buzzy square rejection
        s_error = self._generate_tone(160, 110, 0.18, wave_type='square', decay=4.0)
        if s_error: self.sounds['error'] = s_error

        # 5. Typewriter dialogue chirp: tiny high blip
        s_dialog = self._generate_tone(780, 880, 0.03, wave_type='sine', decay=20.0)
        if s_dialog: self.sounds['dialog'] = s_dialog

        # 6. Fanfare / Mission Complete: 4-note retro triumphant arpeggio (C5, E5, G5, C6)
        s_fanfare = self._generate_chord([523.25, 659.25, 783.99, 1046.50], 0.45)
        if s_fanfare: self.sounds['fanfare'] = s_fanfare

        # 7. Travel sound: whoosh / sweep
        s_travel = self._generate_tone(220, 880, 0.30, wave_type='triangle', decay=2.0)
        if s_travel: self.sounds['travel'] = s_travel

        self.set_volume(self.sfx_volume)

    def set_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for snd in self.sounds.values():
            try:
                snd.set_volume(self.sfx_volume)
            except Exception:
                pass

    def play(self, name: str):
        if not self.enabled or self.sfx_volume <= 0:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass
