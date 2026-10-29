# ECU Studio pour Windows 0.1.0

Installer depuis Applications dans le Mod Center 0.2.0. Ouvrir avec le raccourci
ECU Studio ou le bouton Ouvrir du Mod Center. Lancer BeamNG avec le mod ECU actif
et ouvrir le tuner ECU dans le jeu : la fenêtre se connecte automatiquement.
L’interface provient du mod installé et suit ses mises à jour.

L’application vérifie sa propre version au lancement et redémarre après une mise
à jour valide. Une panne réseau ne bloque pas le tuner local. Les nouvelles
versions n’écrasent jamais le programme en cours.

Prérequis : Windows 10/11 64 bits, Microsoft Edge WebView2 Runtime.
Compilation : Python 3.12, dépendances de requirements-build.txt dans .build-deps,
PyInstaller du Mod Center, puis python ecu-app/build.py.
Le diagnostic --diagnose-tls - vérifie HTTPS et charge le moteur Windows sans
ouvrir de fenêtre. --no-update sert aux essais locaux sans téléchargement.

La fenêtre et son écran d’attente ont été vérifiés sur Windows. Un essai complet
avec une voiture dans BeamNG reste à réaliser.
