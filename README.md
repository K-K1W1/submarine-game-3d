# U-BOOT COMBAT 3D

Ein 3D-U-Boot-Spiel mit Shop, Wasser-Kronen, Uran-Status, Bots und Pausen-Menü.

## Starten

1. Python 3.8+ installieren.
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Spiel starten:
   ```bash
   python main.py
   ```
   oder unter Windows:
   ```bat
   start_game.bat
   ```

## Steuerung

- W/A/S/D: bewegen
- Leertaste: schießen
- X: Shop öffnen
- ESC: Menü/Pause
- C: Spiel speichern

## Spielprinzip

- Start mit 2 U-Booten und 1 Zerstörer
- Wasser-Kronen als Währung
- 3.000 Wasser-Kronen pro zerstörtem Schiff
- Shop zum kaufen von U-Booten und Zerstörern
- Uran-Prozentanzeige steigt mit Schaden
- Maximal 10 Schiffe gleichzeitig; Bots füllen fehlende Plätze

## Projektstruktur

- `main.py` – Spielcode
- `requirements.txt` – Python-Abhängigkeiten
- `start_game.bat` – Windows-Startskript
- `start_game.sh` – Mac/Linux-Startskript

## Lizenz

MIT
