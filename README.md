# Mr14KaraFR Mod Center

Application Windows pour installer et mettre à jour les mods et outils Mr14KaraFR.

[Télécharger le Mod Center 0.3.1](https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases/latest/download/Mr14KaraFR_Mod_Center_0.3.1_Windows.zip)

Extraire tout le ZIP et lancer Mr14KaraFR-Mod-Center.exe avec le dossier _internal à côté.

Cliquer sur **Se connecter avec Discord** et autoriser la connexion dans le navigateur du PC.
Le rôle **Abonné** donne accès aux mods stables dans le Mod Center. Le rôle **Bêta-testeur**
donne accès à la section bêta, séparément ; aucune bêta n’est publiée pour le moment.
Les rôles sont attribués manuellement par le propriétaire.

[Rejoindre le Discord](https://discord.gg/ycc7J8yW3)

Les fichiers restent publics sur GitHub pendant cette phase : le contrôle des rôles
dans l’application ne protège pas les liens directs de téléchargement.
Aucun serveur payant, paiement automatique ou contrôle DRM des mods n’est activé.

- **Mods** : ECU Studio, suspension pneumatique, fumée diesel et flammes HQ.
  Choisir le dossier mods BeamNG et fermer le jeu avant d’installer ou mettre à jour.
- **Applications** : ECU Studio Windows et le Mod Center restent accessibles.
  BeamNG et le mod ECU doivent être ouverts pour utiliser le tuner externe.
  Microsoft Edge WebView2 Runtime est requis pour ECU Studio.

Le Mod Center et ECU Studio se mettent à jour au lancement. À partir de Mod Center 0.2.0,
cette version arrive automatiquement. Les paramètres et les anciennes versions des applications
sont conservés. Les versions 0.1.x nécessitent un dernier téléchargement manuel.

Les téléchargements sont contrôlés par taille et SHA-256 sur HTTPS. Les exécutables
ne sont pas signés numériquement. Les anciens ZIP de mods sont sauvegardés à côté du
dossier mods. Les mods décompressés dans unpacked ne sont pas gérés.

Six logos sont inclus et disponibles dans le pack Logos v2.


## Serveur BeamMP / VPS

Sélectionner le dossier **Resources/Client** dans le Mod Center installé sur le VPS.
Ne pas renommer Client en mods. Arrêter le serveur avant de modifier les ZIP,
puis le redémarrer après installation. Les sauvegardes restent hors de Client.

La version 0.3.1 inclut les certificats Mozilla pour corriger les erreurs HTTPS liées
à un magasin de certificats système incomplet. La vérification HTTPS reste active.
Si l’ancienne version affiche CERTIFICATE_VERIFY_FAILED, télécharger et extraire
manuellement le ZIP corrigé une fois, car cette erreur peut bloquer sa mise à jour automatique.

## Bêta ECU Studio 0.16.22

Mettre à jour le Mod Center en 0.3.2, se connecter à Discord puis choisir **Versions bêta** avec le rôle Bêta-testeur. La version stable de l'ECU reste en 0.16.20. Le téléchargement s'appelle toujours Mr14KaraFR_Programmable_ECU.zip une fois installé.

Le contrôle des rôles est effectué par le Mod Center ; les liens directs GitHub restent publics. Les tests à effectuer sont dans les notes de la release et dans le message préparé pour le canal bêta.
