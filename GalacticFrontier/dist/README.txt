STARSHIP GALACTIC FRONTIER — Windows build
==========================================

RUN THE GAME
  Double-click: Play Galactic Frontier.bat
  Or run: GalacticFrontier.exe

REQUIREMENTS
  - Windows 10/11 (64-bit)
  - Python 3 on PATH (for save data / login backend)
  - One-time: pip install bcrypt

FILES IN THIS FOLDER
  GalacticFrontier.exe     — game (self-contained .NET 8, no separate runtime install)
  bridge_server.py         — backend bridge (do not delete)
  databaselogic.py, database.py, game_data.py — account & galaxy data

REBUILD
  From GalacticFrontier folder: .\publish.ps1

NOTES
  Saves live in game_data.py next to this folder.
  First run may download the Orbitron font (needs internet once).
