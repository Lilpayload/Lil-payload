from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random
import win32api
import win32con
import time

@dataclass
class KeystrokeConfig:
    enabled: bool = True
    min_delay: float = 0.1
    max_delay: float = 0.3
    typing_patterns: List[Dict[str, float]] = field(default_factory=lambda: [
        {"key": "shift", "hold_time": 0.12, "frequency": 0.15},
        {"key": "ctrl", "hold_time": 0.08, "frequency": 0.1},
        {"key": "alt", "hold_time": 0.1, "frequency": 0.05}
    ])
    simulate_mistakes: bool = True
    mistake_frequency: float = 0.02
    common_sequences: List[str] = field(default_factory=lambda: [
        "ls", "dir", "cd ", "pwd", "cls",
        "notepad", "calc", "help"
    ])

class KeystrokeSimulator:
    def __init__(self, config: KeystrokeConfig):
        self.config = config
        self.last_keystroke = time.time()
        self.key_states = {}
        self.common_typos = {
            'a': ['s', 'q', 'w'],
            'b': ['v', 'n', 'h'],
            'c': ['v', 'x', 'd'],
            'd': ['s', 'f', 'e'],
            'e': ['w', 'r', 'd'],
            'f': ['d', 'g', 'r'],
            'g': ['f', 'h', 't'],
            'h': ['g', 'j', 'y'],
            'i': ['u', 'o', 'k'],
            'j': ['h', 'k', 'u'],
            'k': ['j', 'l', 'i'],
            'l': ['k', 'p', 'o'],
            'm': ['n', ',', 'j'],
            'n': ['b', 'm', 'h'],
            'o': ['i', 'p', 'l'],
            'p': ['o', '[', 'l'],
            'q': ['1', 'w', 'a'],
            'r': ['e', 't', 'f'],
            's': ['a', 'd', 'w'],
            't': ['r', 'y', 'g'],
            'u': ['y', 'i', 'j'],
            'v': ['c', 'b', 'g'],
            'w': ['q', 'e', 's'],
            'x': ['z', 'c', 's'],
            'y': ['t', 'u', 'h'],
            'z': ['x', 'a', 's']
        }

    def _generate_human_delay(self) -> float:
        """Generate a human-like delay between keystrokes"""
        base_delay = random.uniform(self.config.min_delay, self.config.max_delay)
        
        # Add random variations
        if random.random() < 0.1:  # 10% chance of longer pause
            base_delay *= random.uniform(2, 4)
        
        # Add slight randomness to simulate natural typing rhythm
        variation = random.gauss(0, 0.02)
        return max(0.01, base_delay + variation)

    def _simulate_mistake(self, text: str) -> str:
        """Simulate common typing mistakes"""
        if not self.config.simulate_mistakes or not text:
            return text

        if random.random() < self.config.mistake_frequency:
            mistake_type = random.choice(['typo', 'double', 'missing'])
            
            if mistake_type == 'typo' and text[-1].lower() in self.common_typos:
                # Replace last character with a common typo
                return text[:-1] + random.choice(self.common_typos[text[-1].lower()])
            elif mistake_type == 'double':
                # Double type a character
                return text + text[-1]
            else:
                # Miss a character
                return text[:-1]
                
        return text

    def generate_typing_sequence(self, command: str) -> str:
        """Generate a human-like typing sequence with potential mistakes"""
        result = []
        buffer = ""
        
        for char in command:
            # Add human-like delay
            time.sleep(self._generate_human_delay())
            
            buffer += char
            
            # Simulate mistakes and corrections
            if random.random() < self.config.mistake_frequency:
                # Make a mistake
                buffer = self._simulate_mistake(buffer)
                result.append(buffer)
                
                # Simulate backspace after mistake
                time.sleep(self._generate_human_delay() * 1.5)
                if len(buffer) > len(result[-1]):
                    buffer = buffer[:-1]
                    result.append(buffer + '\b')
                
            else:
                result.append(buffer)
                
        return ''.join(result)

    def simulate_key_pattern(self, key: str, duration: float):
        """Simulate realistic key press patterns"""
        # Record key press
        self.key_states[key] = time.time()
        
        # Add slight variation to duration
        actual_duration = duration + random.gauss(0, 0.01)
        time.sleep(max(0.01, actual_duration))
        
        # Record key release
        self.key_states[key] = None