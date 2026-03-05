# Critère : Falsification de Signature

La détection de fausses signatures est un levier redoutable pour identifier un document falsifié, car la signature manuscrite est une empreinte biométrique complexe, en plus d’être un élément présent sur presque chaque type de document administratif. Contrairement au texte informatisé qui constitue aujourd’hui la vaste majorité des documents, et contrairement aux logos et tampons d’entreprise qui peuvent être facilement reproduits à l’identique, une signature manuscrite possède des caractéristiques uniques. Lorsqu’un faussaire essaye de reproduire une signature manuscrite, il introduit inévitablement des anomalies microscopiques comme des hésitations dans le tracé ou des tremblements.

La vision par ordinateur peut trouver son rôle ici. Théoriquement, un modèle de Deep Learning serait capable d’apprendre, à partir d’un dataset complet, à séparer si une signature appartient à un certain individu ou non. Nous avons essayé d’implémenter un modèle de segmentation via PyTorch.

### Composition du dossier

Ce dossier est composé :

- d'un notebook _verif_signature.ipynb_ qui réunit d'entièreté du modèle ;
- d'un dossier compressé *data.zip* dont le notebook va extraire les données d'entraînement et de test ;
- d'un dossier *outputs* composé des différents outputs du notebook ;

Le dossier *data.zip* contient 2 dossiers *train* et *validation*, contenant respectivement 50 et 14 auteurs.  
Les auteurs de *train* ont au 12 ou 24 signatures chacun, les auteurs de *validation* ont chacun 12 signatures.

Ce dossier fait 119Mo, il est trop gros pour être stocké sur un git. Voici un lien pour le télécharger : https://drive.google.com/file/d/1yK_QgwBTeLc9ks7Hoz5jUerTVsEmALpg/view?usp=drive_link


Ce dataset a été extrait d'un plus gros dataset provenant d'un hackaton kaggle : https://www.kaggle.com/datasets/robinreni/signature-verification-dataset

### Contenu du notebook

Ce notebook implémente un système de vérification biométrique de signatures manuscrites. Plutôt que d'apprendre à l'IA à reconnaître une liste fixe de personnes (classification), on lui apprend à comparer des images (Metric Learning) pour déterminer si elles ont été signées par la même main.

Ce système s'applique sous 3 axes :

1. La Mécanique du Modèle (L'Encodeur)

   Le cœur du système est un réseau de neurones convolutif (CNN). Il prend une image de signature (nettoyée, mise en noir et blanc, et redimensionnée) et la transforme en un vecteur mathématique de 128 dimensions (appelé embedding). Puis, cette empreinte est "L2-normalisée", ce qui garantit que tous les vecteurs sont sur la même échelle, rendant le calcul des distances parfaitement fiable.

2. La Stratégie d'Entraînement (La Triplet Loss)

   Le modèle s'entraîne en regardant des "triplets" générés dynamiquement à partir des dossiers d'auteurs : une signature de référence (Ancre), une autre vraie signature (Positif) et la signature d'un imposteur (Négatif).

   La fonction d'erreur (Triplet Loss) force l'algorithme à modifier ses paramètres internes pour rapprocher mathématiquement l'Ancre et le Positif, tout en repoussant l'imposteur au-delà d'une marge de sécurité (fixée à 0.5). Le générateur modifie légèrement les images à la volée (rotations, décalages) pour que l'IA se concentre sur le style d'écriture et non sur le placement exact du trait.

3. L'Utilisation Pratique (Le Cycle de Vie)

   Pour intégrer un nouvel utilisateur, le système calcule les embeddings de 5 de ses signatures et en fait une moyenne. Cela crée son Template (profil de référence). Lorsqu'une personne se présente avec une nouvelle signature, le modèle la transforme en vecteur et calcule la distance euclidienne qui la sépare du Template. Si la distance est petite, la porte s'ouvre. Si elle est trop grande, l'accès est refusé.

4. Le Bilan des Performances Actuelles

   On a fait une évaluation sur 1400 paires de signatures et tracé la courbe ROC. Le diagnostic est clair :

   Le positif (AUC de 0.883) : Le modèle fonctionne. Il a fondamentalement compris comment faire la différence entre les styles d'écriture et surpasse largement le hasard. Il a d'ailleurs parfaitement bloqué l'imposteur lors du test de bout en bout.

   La limite actuelle (EER de 19,4%) : Au meilleur de ses capacités actuelles, l'IA se trompe encore environ 1 fois sur 5. Le seuil optimal d'acceptation a été calculé à 0.41, mais le modèle manque encore de subtilité : il a tendance à rejeter de vrais utilisateurs (comme le cas de l'utilisateur 056) car il juge les variations naturelles de leur écriture trop importantes.

### Lancement du notebook

Je ne conseille pas d'exécuter les différentes parties du notebook, car le code entier prend plusieurs heures (cellule 11 a pris 3h sous Colab).  
Sinon, l'installation des bibliothèques et le fonctionnement du code sont expliqués dans le notebook.