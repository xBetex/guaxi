# Project Structure: Guaxinim Tempo Real (Full Modular + Panache)

```text
guaxinim_tempo_real/
├── config.py              # Centralized themes, colors, and constants (Python)
├── game.py                # Main execution script (Python version)
├── index.html             # Entry point (Web version)
├── script.js              # Core game logic, Panache Graphics Engine (Web version)
├── sprites.py             # ASCII art templates (Python version)
├── style.css              # Glassmorphic UI and layout styles
├── requirements.txt       # Python dependencies
├── ässets/                # Image assets (PNGs)
└── old_versions/          # Backup of previous single-file versions
```

---

# Consolidated Codebase (Web)

## script.js Highlights
*   **Glow Engine**: Added `shadowBlur` and radial gradients for the Sun, Moon, and Bonfire.
*   **Dynamic Floor**: Implemented a vertical gradient for the grass (`SEASON_COLORS`) with textured tufts and shadows for "panache".
*   **Atmospheric Effects**: Restored fireflies and flickering bonfire logic.

(Full code available in the file system)
