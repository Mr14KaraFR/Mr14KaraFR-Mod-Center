# Mod Center 0.3.1 — serveur BeamMP et HTTPS sur VPS

Le Mod Center accepte maintenant le dossier **Resources/Client** d’un serveur BeamMP, en plus du dossier **mods** de BeamNG. Le dossier Client ne doit pas être renommé.

1. Arrêter le serveur BeamMP.
2. Dans le Mod Center installé sur le VPS, cliquer sur Parcourir et sélectionner Resources/Client.
3. Installer ou mettre à jour les mods, puis redémarrer le serveur.

Les ZIP restent compressés dans Client. Les sauvegardes sont placées dans Resources/Mr14KaraFR-backups, en dehors des fichiers distribués aux joueurs. Les plugins Resources/Server et les fichiers Client/repo ne sont pas modifiés.
L’application bloque les écritures lorsqu’un processus Windows standard BeamMP-Server*.exe est détecté et vérifie à nouveau avant le remplacement.

## Correction HTTPS

Le jeu de certificats Mozilla de Certifi 2026.10.19 est embarqué pour les VPS dont les certificats racines système sont incomplets. Les téléchargements, mises à jour et connexions Discord l’utilisent en complément du magasin système. La vérification des certificats et du nom d’hôte reste active.

Si la version 0.3.0 affiche déjà CERTIFICATE_VERIFY_FAILED, télécharger manuellement **Mr14KaraFR_Mod_Center_0.3.1_Windows.zip** une fois, extraire tout le ZIP et lancer le nouvel EXE avec son dossier _internal. La mise à jour automatique de l’ancienne version peut être bloquée par cette même erreur HTTPS.

Les accès Discord, les fichiers publics GitHub et les versions des quatre mods restent inchangés. Cette mise à jour ne configure pas protectmod ni un hébergement privé.

## Validation

62 tests automatiques réussis, dont installation et mise à jour dans un faux serveur BeamMP, sauvegardes hors de Client, refus d’écriture avec serveur actif et chargement des certificats sans magasin système. GitHub et l’API publique Discord ont été joints avec les certificats embarqués et la validation HTTPS active. Le véritable EXE Windows a passé son diagnostic TLS. Aucun fichier du VPS ou du jeu n’a été modifié pendant ces tests.
