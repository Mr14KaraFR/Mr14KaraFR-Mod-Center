# Mr14KaraFR Mod Center

Application Windows pour installer et mettre à jour les quatre mods publics **Mr14KaraFR** pour BeamNG.drive.

## Télécharger et installer

Ouvrir la **[dernière publication](https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases/latest)** et télécharger l’archive **Mr14KaraFR_Mod_Center_…_Windows.zip**.

1. Extraire **tout le ZIP** dans un dossier.
2. Ouvrir **Mr14KaraFR-Mod-Center.exe** et conserver le dossier **_internal** à côté.
3. Choisir le dossier **mods** du dossier utilisateur BeamNG avec **Parcourir**.
4. Fermer BeamNG, puis cliquer sur **Installer** pour les mods souhaités.

Le catalogue officiel est déjà configuré. Les versions sont vérifiées à l’ouverture du Mod Center et avec **Vérifier les mises à jour**. Le bouton **Tout mettre à jour** concerne uniquement les mods déjà installés.

## Les quatre mods

- **ECU Studio** : calculateur moteur, cartographies et profils.
- **Suspension pneumatique** : réglages de hauteur, profils et commandes.
- **Fumée diesel volumétrique** : fumée volumétrique et effets d’échappement.
- **Flammes & détonations HQ** : flammes volumétriques et effets sonores.

## Sauvegardes

Les anciennes archives reconnues dans `mods` et `mods/repo` sont sauvegardées dans **Mr14KaraFR-backups**, à côté du dossier `mods`, avant remplacement. Chaque sauvegarde contient un `restore.json` avec les emplacements d’origine. Les mods décompressés dans `unpacked` ne sont pas gérés.

Les téléchargements sont vérifiés par leur taille, leur SHA-256, l’intégrité du ZIP et les métadonnées du mod. Une version locale plus récente n’est pas rétrogradée. L’application n’est pas signée numériquement et ne se met pas elle-même à jour automatiquement.

## Android et Discord

L’application Android AIR reste disponible dans son dépôt dédié : **[Mr14KaraFR-Air-Remote](https://github.com/Mr14KaraFR/Mr14KaraFR-Air-Remote)**.

Un lien vers le futur serveur Discord dédié aux mods pourra être ajouté dans les paramètres du Mod Center.

## Publication des nouvelles versions

Les ZIP d’une publication et son `catalog.json` sont conservés ensemble. Chaque URL de mod désigne une publication précise. La publication est d’abord préparée en brouillon ; le lien de dernière version n’est déplacé qu’une fois les sept fichiers vérifiés et transférés.

Ce dépôt contient les fichiers publics de distribution et le processus de publication. Aucune clé privée ni information de connexion n’est nécessaire dans l’application.
