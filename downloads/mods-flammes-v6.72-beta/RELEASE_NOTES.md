# Flammes HQ 6.72 — bêta de composition avec les vitres

Dans Mod Center, ouvrir Versions bêta puis choisir « Flammes HQ — essai vitres ». Le ZIP installé garde le nom volumetric_backfire_HQ.zip. Fermer BeamNG avant installation puis redémarrer le jeu.

Cette révision compose les flammes après ObjTranslucentBin : le verre et sa réfraction ne doivent plus redessiner par-dessus une émission située devant une vitre. Le réglage est aussi réappliqué si le PostEffect existe déjà lors d’un rechargement Lua.

Les shaders de volume, les formes, les mouvements, les tailles, les sons, les collisions, les conditions de déclenchement et les budgets de rendu sont identiques à la 6.71. Le clipping par profondeur opaque reste actif.

Validation effectuée sans lancer ni contrôler le jeu : compilation de tous les Lua et du shader VS/PS, initialisation d’un PostEffect neuf et réutilisé, nettoyage des objets et vérification du ZIP. Pas de contrôle visuel en jeu pour cette révision. Vérifier les flammes devant et derrière le pare-brise, les vitres latérales, la vue habitacle, la nuit et le brouillard. La composition après les transparents ne calcule pas une transmission du verre triée par profondeur ; l’aspect des flammes derrière le verre peut différer. Cette version reste en bêta en attendant l’essai visuel.

Les quatre versions stables, les deux applications Windows et les bêtas ECU 0.16.23 / fumée diesel 0.9.22 sont conservées. Les empreintes de leurs archives restent identiques. Aucun fichier du jeu de l’utilisateur n’a été remplacé pendant sa partie.
