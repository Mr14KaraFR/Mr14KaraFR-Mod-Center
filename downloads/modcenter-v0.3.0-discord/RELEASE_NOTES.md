# Mod Center 0.3.0 — connexion Discord

Le Mod Center demande désormais une connexion Discord pour installer ou mettre à jour les mods réservés dans son interface. Il vérifie les rôles du serveur Mr14KaraFR avant chaque téléchargement.

- **Abonné** : accès aux mods stables.
- **Bêta-testeur** : accès à la section bêta, séparée de l’abonnement. Aucune version bêta n’est publiée pour le moment.
- **Propriétaire** : accès aux deux sections.
- **Pas abonné** : catalogue visible, installations et mises à jour réservées bloquées dans le Mod Center.

Au premier lancement, cliquer sur **Se connecter avec Discord**, puis autoriser la connexion dans le navigateur du PC. La connexion demande uniquement le profil de base et les informations de membre du serveur. Les jetons restent en mémoire et une nouvelle connexion est nécessaire après fermeture.

**Phase GitHub publique :** les ZIP et leurs liens directs restent publics. Le contrôle dans le Mod Center ne protège pas ces liens et peut être contourné en téléchargeant les fichiers ailleurs. L’hébergement privé est reporté ; aucun abonnement de serveur ni paiement automatique n’est activé. Les rôles sont attribués manuellement par le propriétaire.

Le Mod Center et ECU Studio continuent leurs mises à jour publiques. Le Mod Center 0.2.0 et versions suivantes récupèrent cette nouvelle version automatiquement au lancement. Les mods déjà installés restent sur le PC ; une version locale plus récente n’est pas rétrogradée.

Les quatre versions de mods publiées sont conservées : ECU 0.16.20, suspension 0.16.1, fumée diesel 0.9.20 et flammes HQ 6.71.0-HQ. ECU Studio Windows reste en 0.1.1.

## Première installation

Télécharger **Mr14KaraFR_Mod_Center_0.3.0_Windows.zip**, extraire tout le ZIP puis lancer **Mr14KaraFR-Mod-Center.exe** en conservant le dossier **_internal** à côté. Choisir le dossier mods de BeamNG et fermer le jeu avant toute installation. Les exécutables ne sont pas signés numériquement.

## Validation

49 tests automatiques passent : PKCE, retour local de connexion, contrôle des rôles, retrait de rôle, isolation des identifiants Discord, installations et sauvegardes. Les vrais EXE 0.2.2 et 0.3.0 ont passé leur diagnostic TLS lors d’une mise à jour dans un dossier de test distinct du jeu. La première autorisation réelle du compte dans le navigateur reste à effectuer.
