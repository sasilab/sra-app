# SRAandTools

Das hier ist die Code-Dokumentation für den SRA und das grafische User-Interface.

## Installation

Zunächst muss das Repository von Gitlab heruntergeladen werden (falls noch nicht geschehen, bitte die Anleitung in den
Teams-Dateien beachten). Anschließend müssen alle Python-Bibliotheken installiert werden. Alle verwendeten Bibliotheken
sind in der `requirements.txt`-Datei aufgeführt. Diese können installiert werden, indem folgender Befehl in das Terminal
geschrieben wird.

```bash
pip install -r requirements.txt
```

## Start des User-Interfaces

Anschließend muss das User-Interface gestartet werden. Das UI wurde mit Streamlit gebaut und muss daher mit Streamlit
gestartet werden. Für den Start einfach folgenden Befehl in das Terminal einfügen. Anschließend wird das UI gestartet
und automatisch geöffnet.

```bash
streamlit run app.py
```


### (Optional) Umgebungsvariablen einrichten

Für die Verwendung der SMA-Wechselrichter API sowie des Forecasts von pvnode, müssen ein paar Umgebungsvariablen
eingerichtet werden. Ich empfehle dazu die Verwendung von python-dotenv. Bitte dazu mit pip installieren:

```bash
pip install python-dotenv
```

Dann eine Datei mit dem Namen `.env` im Projektordner `SRAandTools` lokal erstellen. In die Datei werden die
Umgebungsvariablen eingefügt:

```
API_KEY=
username_SMA=
pwd_SMA=
```

`API_KEY` ist der API-Key von pvnode. `username_SMA` ist der Username für das Login bei SMA. Und `pwd_SMA` ist das
Passwort für den Login bei SMA.


## Dokumentation
Dazu einfach die Datei `index.html` im Ordner `docs` im Browser öffnen!

1. Pfad im Explorer öffnen (`SRAandTools/docs/index.html`)
2. Rechtsklick -> Öffnen in -> Euren Standardbrowser auswählen
