# Mod Center 0.3.2 — première distribution bêta ECU

Canal bêta configuré séparément : ECU 0.16.22 uniquement dans Versions bêta, après vérification du rôle Discord Bêta-testeur (ou propriétaire). Le catalogue stable reste à ECU 0.16.20 ; fumée, flammes et suspension conservent leurs versions publiées. Les droits sont revérifiés avant chaque téléchargement.

Le Mod Center utilise toujours GitHub public. Le contrôle par rôle s'applique dans l'application ; un lien direct partagé reste téléchargeable sans authentification. Ce n'est pas un hébergement privé.

Le nouveau canal exige la mise à jour du Mod Center 0.3.1 vers 0.3.2, qui configure catalog-beta.json. Les téléchargements de mods et la publication distante ne sont pas effectués par la compilation locale.

# Mod Center 0.3.1 — serveur BeamMP et certificats HTTPS

Sélectionne soit le dossier mods de BeamNG, soit le dossier Resources/Client du serveur BeamMP.
Ne renomme pas Client en mods : BeamMP utilise cette structure.
Pour un VPS, lancer le Mod Center sur le VPS (ou sélectionner un partage réellement accessible) ;
un chemin C: distant n’est pas automatiquement accessible depuis ton PC.

Arrêter le serveur BeamMP avant toute installation ou mise à jour, puis le redémarrer.
Le Mod Center détecte les processus Windows standards BeamMP-Server*.exe et bloque
l’écriture tant qu’un serveur est détecté, avec une seconde vérification après téléchargement.
Il n’arrête ni ne redémarre le serveur automatiquement.
Les ZIP restent compressés dans Client. Les sauvegardes vont dans Resources/Mr14KaraFR-backups,
en dehors des fichiers distribués aux joueurs. Resources/Server et les plugins ne sont pas modifiés.
Le dossier Client/repo n’est pas traité comme le dossier repo de BeamNG.

Le jeu de certificats Mozilla issu de Certifi est inclus pour les VPS dont le magasin
de certificats racines Windows est incomplet. Les téléchargements, mises à jour et
connexions Discord l’utilisent en complément des certificats système.
La vérification des certificats et du nom d’hôte reste obligatoire.
Si l’ancienne application est déjà bloquée par CERTIFICATE_VERIFY_FAILED, un téléchargement
manuel du ZIP corrigé peut être nécessaire une fois ; la mise à jour automatique
utilise elle aussi HTTPS et ne peut pas contourner cette erreur.

Les accès Discord et les téléchargements publics GitHub restent ceux de la 0.3.0.
Cette correction ne configure pas la commande protectmod et ne rend pas les fichiers privés.

# Mod Center 0.3.0 — connexion Discord, distribution GitHub

Cette version contrôle l’accès dans le Mod Center avec une véritable connexion Discord
OAuth2 / PKCE et les rôles du serveur Mr14KaraFR. Aucun hébergement R2 ou VPS n’est nécessaire
pour cette phase. Les fichiers GitHub restent publics et ce filtrage dans l’application
n’est pas une protection des liens de téléchargement.

- Abonné : installation et mises à jour des mods stables dans le Mod Center.
- Bêta-testeur : accès à la section bêta, indépendante de l’abonnement.
- Propriétaire identifié : les deux accès sans modifier les rôles Discord.
- Non connecté / Pas abonné : catalogue visible, téléchargements réservés dans l’application.
- Retrait de rôle : vérifié à nouveau avant chaque téléchargement.
- Les fichiers déjà installés restent sur le PC.
- Le Mod Center et ECU Studio continuent de se mettre à jour publiquement.
- Aucune bêta n’est affichée tant qu’un vrai catalogue bêta n’a pas été publié.
- Les rôles et abonnements restent attribués manuellement par le propriétaire.

## Configuration Discord

Application ID : 1565374469550116864.
Portail : OAuth2, activer Public Client et enregistrer exactement
http://127.0.0.1:47619/callback comme redirection.
Les scopes demandés sont identify et guilds.members.read.
Le retour ne reçoit que le code OAuth à usage unique, avec vérification de state et iss.
Le service local écoute seulement sur 127.0.0.1 et se ferme après connexion/annulation.
Les jetons utilisateur restent en mémoire pendant cette ouverture de l’application.
Aucun Client Secret, jeton de bot ou mot de passe n’est embarqué ; aucun jeton Discord
n’est envoyé à GitHub. Le compte doit être connecté à nouveau après fermeture.

La configuration publique est dans channel.json, bloc discord_auth.
Le futur accès privé côté serveur reste préparé séparément dans ../private-access/.
Une migration future devra protéger les téléchargements côté serveur ; ce pilote
autorise seulement le contrôle de l’interface avec des fichiers publiquement accessibles.

## Essai avant publication générale

Les tests locaux ne prouvent pas que les réglages du portail ont été enregistrés.
Vérifier une connexion réelle dans le navigateur du PC, puis les rôles Abonné,
Bêta-testeur, les deux, Pas abonné et le retrait de rôle. Ne jamais mettre de jeton
Discord dans un rapport de diagnostic ou une capture à partager.

# Mr14KaraFR Mod Center — Windows 0.2.2

## Logo flammes 0.2.2

La flamme remplit désormais toute l’ouverture de la sortie d’échappement.
Le pack Logos v2 conserve les cinq autres logos et remplace celui des flammes.
ECU Studio Windows reste à la version 0.1.1.

## Logos 0.2.1

Six logos : Mod Center, ECU Studio Windows, mod ECU, suspension pneumatique,
fumée diesel et flammes HQ. Les icônes Windows et les cartes du catalogue utilisent
les visuels embarqués. Le pack PNG transparents et ICO est distribué avec la release.
ECU Studio Windows 0.1.1 utilise son icône dans l’exécutable et l’écran de connexion.

## Applications Windows et mises à jour automatiques

Deux sections : **Mods** pour les archives BeamNG, **Applications** pour ECU Studio
et le Mod Center. Installer une application ne demande pas de dossier mods et ne
modifie pas le jeu. ECU Studio a sa propre fenêtre WebView2, un raccourci sur le
bureau et un écran de connexion automatique à BeamNG. Le mod ECU doit être actif ;
ouvrir son tuner dans le jeu démarre la liaison locale.

Le Mod Center et ECU Studio vérifient leurs nouvelles versions au lancement.
Une nouvelle version est téléchargée, contrôlée (taille, SHA-256, chemins ZIP,
identité/version), extraite et testée avec son vrai EXE avant activation.
Les versions précédentes restent présentes. Hors ligne ou si le téléchargement
échoue, la version existante reste utilisable. Les anciens raccourcis suivent
la version activée, même hors ligne. Aucun service ne tourne quand les apps sont fermées.

Les fichiers des applications sont dans
`%LOCALAPPDATA%/Mr14KaraFR/Applications/<id>/versions/`.
Les paramètres du Mod Center restent dans leur dossier habituel.
Les mises à jour des mods restent déclenchées par les boutons, jeu fermé.
Le bouton **Tout mettre à jour** concerne la section active et seulement les
éléments déjà installés.

**Migration 0.1.2 :** télécharger et extraire la 0.2.0 une dernière fois. Le mécanisme
automatique est absent des anciennes versions. À partir de 0.2.0, les prochaines
versions du Mod Center se téléchargent et redémarrent automatiquement au lancement.
Les ZIP et le catalogue doivent être publiés ensemble via prepare_github.py.

Compilation : compiler ecu-app/build.py puis mod-center/build.py et exécuter
mod-center/prepare_github.py. Le catalogue schema 1 conserve les quatre mods et
ajoute une liste applications ; les anciens Mod Centers continuent à lire les mods.
Les paquets d’applications contiennent application.json et leur EXE à la racine.
Microsoft Edge WebView2 Runtime est requis pour ECU Studio.
Les EXE ne sont pas signés ; la confiance repose sur le catalogue HTTPS officiel.

## Historique 0.1.2

Application pour installer et mettre à jour les quatre mods publics : ECU Studio,
suspension pneumatique, fumée diesel et flammes HQ. L’outil vérifie le catalogue
à son ouverture, puis installe les mods choisis lorsque le joueur clique sur le bouton.
Il ne tourne pas en arrière-plan quand il est fermé.

## Correction 0.1.2 du démarrage Windows

Le paquet 0.1.1 omettait un fichier PEM requis par le module SSL du Python utilisé
pour compiler l’application. Le premier accès HTTPS échouait avec
`[Errno 2] No such file or directory`. La version 0.1.2 inclut ce fichier ; les
contrôles de certificat et de nom d’hôte sont conservés.

La compilation exécute désormais le véritable EXE avec `--diagnose-tls -`, sans
réseau, sans fenêtre et sans écriture de rapport. Le workflow GitHub teste ensuite
le ZIP et le véritable EXE sur Windows avant de publier la release, avec une lecture
du catalogue public. `--diagnose <fichier.json>` permet un diagnostic local plus
détaillé ; `--diagnose -` utilise uniquement le code de sortie et ne modifie pas les mods.
Les erreurs des opérations sont aussi consignées localement dans `errors.log`,
à côté des paramètres, lorsque ce dossier est accessible en écriture.

## Essayer la première version

Ouvrir `dist/0.1.2/Mr14KaraFR-Mod-Center/Mr14KaraFR-Mod-Center.exe`.
Conserver le dossier `_internal` à côté de l’EXE : ce prototype est portable,
le joueur n’a pas besoin d’installer Python.

Le catalogue GitHub officiel est intégré dans `channel.json` :
`https://github.com/Mr14KaraFR/Mr14KaraFR-Mod-Center/releases/latest/download/catalog.json`.
Le joueur n’a rien à saisir. Pour un essai local indépendant de GitHub :

1. Cliquer sur **Paramètres**, puis **Catalogue local (test)**.
2. Choisir `outputs/mod-center-release/catalog.json` dans le projet.
3. Les quatre mods et leurs versions apparaissent depuis les ZIP existants.
4. Pour tester sans toucher au jeu, créer un dossier vide appelé `mods` et le sélectionner.
5. Pour une installation réelle, ouvrir le dossier utilisateur depuis le lanceur BeamNG,
   puis sélectionner son dossier `mods` avec **Parcourir**. Fermer le jeu avant l’installation.

**Tout mettre à jour** concerne uniquement les mods déjà installés.
Un nouveau mod s’installe avec son bouton **Installer**.
Les ZIP restent compressés, comme attendu par BeamNG.

## Publier les futures mises à jour

Les archives utilisées sont les quatre ZIP à la racine du projet. Leur numéro de version
est lu dans `mod_info/<identifiant>/info.json`, pas déduit de leur nom.

Après avoir reconstruit les ZIP, avec un nouveau numéro de version :

```powershell
python mod-center/publish.py --notes "Description des nouveautés"
```

Cette commande produit les ZIP et `catalog.json` dans `outputs/mod-center-release/`.
Elle n’envoie rien sur Internet. Les noms des téléchargements contiennent la version
et une empreinte ; le nom installé dans BeamNG reste stable.

Héberger les fichiers sur un serveur public HTTPS avec des liens directs et stables.
Envoyer d’abord les nouveaux ZIP, puis remplacer `catalog.json` en dernier.
Garder les anciens ZIP disponibles pour les téléchargements déjà démarrés.
Configurer le serveur pour revalider le catalogue (ex. `Cache-Control: no-cache`).
Les liens de pièce jointe Discord ne sont pas utilisés comme hébergement permanent.

Dans **Paramètres**, renseigner l’adresse HTTPS de `catalog.json`.
Pour que les nouveaux joueurs n’aient rien à saisir, mettre cette adresse dans
`channel.json` puis reconstruire l’application avant de la distribuer.
L’hébergement retenu est **GitHub Releases**, dans le dépôt
`Mr14KaraFR/Mr14KaraFR-Mod-Center`. Le dépôt Android reste indépendant.

Pour préparer une publication GitHub complète après compilation :

```powershell
python mod-center/build.py
python mod-center/prepare_github.py --tag modcenter-v0.1.1
```

Pour une publication ultérieure, utiliser un **nouveau tag**. Ne jamais modifier
les ZIP d’une publication existante. Le script prépare les quatre ZIP de mods,
le catalogue avec des adresses liées à ce tag, l’application Windows et les empreintes
dans `outputs/mod-center-github-releases/<tag>/`.

La publication distante utilise les fichiers de distribution, `publication/release.json`
et le workflow du dépôt. Celui-ci vérifie les sept fichiers, prépare une release en
brouillon, transfère tous les fichiers, puis la publie comme dernière version.
Le lien `releases/latest/download/catalog.json` bascule seulement à cette dernière étape.
Les identifiants GitHub ne sont jamais intégrés à l’application.

## Discord et évolution

Le lien d’invitation est facultatif et modifiable dans **Paramètres**.
Un nouveau Discord dédié aux mods pourra donc être ajouté plus tard.
Ces paramètres sont enregistrés dans `%LOCALAPPDATA%/Mr14KaraFR/ModCenter/settings.json`.
Un catalogue de test n’est jamais mémorisé comme adresse publique.
Une distribution privée demanderait une authentification et un serveur contrôlant
l’accès aux téléchargements. Cette version est publique, sans compte.

## Remplacement et sauvegardes

L’application vérifie la taille, le SHA-256, l’intégrité du ZIP, l’identifiant du mod
et sa version avant de remplacer quoi que ce soit. Une version locale plus récente
n’est pas rétrogradée. Une autre installation simultanée est bloquée.

Les anciennes archives identifiées comme le même mod dans `mods` ou `mods/repo`
sont sauvegardées dans `Mr14KaraFR-backups`, à côté du dossier `mods`, avant
le remplacement et le retrait des doublons. Chaque sauvegarde comporte un
`restore.json` indiquant le chemin d’origine. La restauration est manuelle : fermer
le jeu, déplacer le nouveau ZIP de côté et recopier les sauvegardes à leurs emplacements.
En cas d’erreur de remplacement, l’outil tente de restaurer les fichiers concernés.
Une coupure du PC pendant l’écriture peut nécessiter une restauration manuelle.

Les mods décompressés dans `unpacked` et les doublons situés ailleurs ne sont pas gérés.
L’application refuse de modifier les mods quand elle détecte un processus BeamNG.
Ne pas lancer le jeu pendant l’opération.

Le SHA-256 détecte les fichiers incomplets ou différents du catalogue. Ce prototype
fait confiance à l’hébergeur HTTPS : il ne comporte pas de signature indépendante
du catalogue. L’EXE n’est pas signé numériquement. Depuis la 0.2.0, la mise à jour de l’application est automatique au lancement.

## Développement

Python 3.12 avec Tkinter. Aucun paquet tiers requis pour lancer les sources :

```powershell
python mod-center/app.py
python -m unittest discover -s mod-center -p test_core.py -v
python -m pip install --target mod-center/.build-deps pyinstaller==6.22.3
python mod-center/build.py
```

Les tests créent de faux mods dans des dossiers temporaires : ils ne modifient
pas l’installation BeamNG du joueur. Ils couvrent installation, mise à jour,
sauvegarde, doublons, annulation en cas de fichier invalide, refus de rétrogradation,
verrouillage et restauration après une erreur de remplacement.

Références : [installation des mods BeamNG](https://documentation.beamng.com/tutorials/mods/installing-mods/),
[distribution avec PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).
