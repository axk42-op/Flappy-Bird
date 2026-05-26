# STARSHIP GALACTIC FRONTIER

Sci-fi space game with a **WPF** frontend (C#) and **Python** backend (accounts, galaxy, saves).

## Quick start (WPF)

**Requirements:** Windows 10/11, [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0), Python 3, `pip install bcrypt`

```powershell
cd GalacticFrontier
.\publish.ps1
cd dist
.\Play Galactic Frontier.bat
```

Or develop:

```powershell
cd GalacticFrontier
dotnet run --project GalacticFrontier\GalacticFrontier.csproj
```

Copy `game_data.example.py` to `game_data.py` in the repo root before first run.

## Legacy tkinter UI

```powershell
pip install bcrypt
python launcher.py
```

## Layout

| Path | Role |
|------|------|
| `GalacticFrontier/` | WPF app (MVVM) |
| `bridge_server.py` | JSON IPC for WPF ↔ Python |
| `database.py`, `databaselogic.py` | Users & galaxy persistence |
| `game_data.py` | Save file (gitignored) |
| `launcher.py`, `combat.py`, … | Original tkinter UI |

## License

Findora Source Available License (FSAL) v1.0 — see [LICENSE](LICENSE).
