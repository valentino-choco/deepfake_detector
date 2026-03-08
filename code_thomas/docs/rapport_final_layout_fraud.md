# Rapport final — refonte fidèle du projet de détection de fraudes documentaires

## 1. Objet

Ce livrable final répond explicitement aux remarques fonctionnelles suivantes :

1. comparer la mise en page à une structure de référence ;
2. vérifier l'ordre des sections et la présence des champs obligatoires ;
3. analyser les incohérences d'alignement ;
4. détecter les décalages de logos ;
5. détecter les incohérences d'en-tête et de pied de page ;
6. repérer les champs de texte à des emplacements inattendus ;
7. repérer les polices non standard.

Le point essentiel est que le projet final ne se contente pas d'un nettoyage du notebook : il **réimplémente** les analyses de mise en page manquantes dans un package Python lisible, testable et documenté.

## 2. Diagnostic de départ

Le notebook d'origine contenait déjà des briques riches :
- comparaison à une structure de référence ;
- analyse d'alignement ;
- contrôle des champs sémantiques ;
- cohérence header/footer ;
- détection de zones graphiques ;
- cohérence multi-pages ;
- analyse de polices par zone et au niveau PDF.

Une partie de ces briques avait disparu dans une version intermédiaire plus orientée scoring local. Le présent livrable corrige ce point et restaure la logique initiale dans une architecture modulaire.

## 3. Architecture retenue

Voir la figure `pipeline_diagram.png` et le fichier `docs/FINAL_ARCHITECTURE.md`.

L'architecture finale suit la chaîne suivante :

- ingestion ;
- sections de référence ;
- champs mal positionnés ;
- alignement et espacement ;
- polices ;
- indices visuels (header/footer, logos, densité d'encre) ;
- cohérence multi-pages ;
- revue locale des candidats numériques ;
- score d'authenticité final.

## 4. Réimplémentation par remarque

### 4.1 Comparer la mise en page à une structure de référence

Implémentation :
- `src/docfraud_layout/reference_data.py`
- `src/docfraud_layout/layout_reference.py`

Contenu :
- sections attendues par type documentaire ;
- zones Y normalisées ;
- mots-clés par section ;
- champs obligatoires ;
- contrôle de couverture.

Sortie :
- sections détectées ;
- sections manquantes ;
- anomalies `section_manquante` et `ordre_sections`.

### 4.2 Analyse de l'ordre des sections et des champs obligatoires

L'analyse ne s'arrête pas à la présence. Pour chaque section détectée, une position verticale observée est estimée. Le pipeline compare ensuite l'ordre des centres observés avec l'ordre théorique du gabarit. Toute inversion produit une anomalie `ordre_sections`.

### 4.3 Analyse des incohérences d'alignement

Implémentation :
- `src/docfraud_layout/layout_alignment.py`

Deux niveaux :
- colonnes dominantes globales ;
- désalignements par section.

Le module mesure aussi la régularité des espacements verticaux. On obtient ainsi :
- `alignement_global`
- `alignement_section`
- `espacement_irregulier`

### 4.4 Décalage dans les logos

Implémentation :
- `src/docfraud_layout/visual_layout.py`
- `src/docfraud_layout/multipage.py`

Les zones graphiques sont détectées par densité de gradient dans une grille, en pénalisant les cellules riches en texte OCR. Pour les documents avec un gabarit connu, la position attendue du logo est définie dans `reference_data.py`. Cela permet de produire :
- `logo_absent`
- `logo_decale`
- `logo_flou`
- `logo_decale_multipage`

### 4.5 Incohérence dans les en-têtes / pieds de page

Implémentation :
- `src/docfraud_layout/visual_layout.py`
- `src/docfraud_layout/multipage.py`

Deux approches sont combinées :
- comparaison visuelle header/body/footer par variance du Laplacien et ELA ;
- comparaison textuelle des signatures d'en-tête et de pied de page entre pages.

### 4.6 Champs de texte à des emplacements inattendus

Implémentation :
- `src/docfraud_layout/layout_reference.py`

Le module `analyze_field_positions` compare les mots-clés forts à une zone Y attendue. Il produit des anomalies `champ_mal_positionne`. C'est la réponse directe à la remarque sur les champs de texte inattendus.

### 4.7 Utilisation de polices non standard

Implémentation :
- `src/docfraud_layout/font_analysis.py`

Le projet couvre :
- variation globale des hauteurs de texte ;
- cohérence des tailles par zone ;
- rareté de familles de polices ;
- polices OCR/PDF non standard ;
- familles embarquées dans les PDF.

Catégories typiques :
- `tailles_police_multiples`
- `police_zone`
- `police_non_standard`
- `police_rare`
- `police_famille_pdf`

## 5. Organisation du code

Le code a été séparé pour être relu facilement :

- `reference_data.py` : gabarits et zones attendues
- `layout_reference.py` : sections + champs
- `layout_alignment.py` : alignement + espacement
- `font_analysis.py` : polices OCR et PDF
- `visual_layout.py` : indices visuels
- `multipage.py` : cohérence entre pages
- `candidate_signals.py` : revue locale par candidats
- `pipeline.py` : orchestration

Cette organisation rend le projet beaucoup plus simple à expliquer à des relecteurs qu'un notebook monolithique.

## 6. Exemple de sortie

L'exemple `examples/sample_doc.json` a été construit pour produire au moins :
- un champ mal positionné (`SIRET`) ;
- une police inhabituelle (`Courier`) ;
- une perturbation légère d'alignement.

Le script :

```bash
python scripts/run_analysis.py --document examples/sample_doc.json --output analysis_report.json
```

produit un score d'authenticité et une liste d'anomalies hiérarchisées.

## 7. Positionnement scientifique



- DTD / DocTamper (CVPR 2023) a montré l'intérêt de combiner indices visuels et fréquentiels dans les documents ;
- FFDN (ECCV 2024) renforce cette intuition en améliorant la fusion fréquentielle ;
- CSIAD (ACL 2025) montre qu'un LLM est plus crédible en couche d'analyse logique croisée qu'en juge visuel unique ;
- AIForge-Doc (2026) souligne que les faux par inpainting génératif sur champs numériques forment une nouvelle classe d'attaques ;
- DOCFORGE-BENCH (2026) montre que la calibration est un verrou majeur pour le passage du labo au terrain.

Le présent projet ne prétend pas reproduire DTD ou FFDN. Il met plutôt en place une base de revue humaine robuste, lisible et extensible.

## 8. Datasets recommandés

Pour les essais futurs :
- DocTamper ;
- Find it Again! ;
- CORD ;
- XFUND.

AIForge-Doc est référencé comme benchmark scientifique moderne, mais le projet final n'en dépend pas pour fonctionner.

## 9. Tests et validation

Les vérifications minimales fournies dans le dépôt sont :
- installation par `pip install -e .` ;
- test `pytest` ;
- analyse du JSON d'exemple ;
- analyse d'une image d'exemple ;
- benchmark simple sur manifeste JSONL.

## 10. Limites

Le projet ne remplace pas :
- un vrai segmentateur appris de régions falsifiées ;
- un modèle RGB + DCT entraîné ;
- une calibration fondée sur un jeu de validation représentatif.

Les heuristiques d'alignement restent volontairement lisibles. Elles doivent être considérées comme une couche de détection et d'explication, pas comme une preuve forensique définitive.
1. Références

- Qu et al., 2023, *Towards Robust Tampered Text Detection in Document Image: New Dataset and New Solution*, CVPR.
- Chen et al., 2024, *Enhancing Tampered Text Detection through Frequency Feature Fusion and Decomposition*, ECCV.
- Wang et al., 2025, *Innovative Image Fraud Detection with Cross-Sample Anomaly Analysis: The Power of LLMs*, ACL.
- Wu et al., 2026, *AIForge-Doc: A Benchmark for Detecting AI-Forged Tampering in Financial and Form Documents*, arXiv.
- Zhao et al., 2026, *DOCFORGE-BENCH: A Comprehensive Benchmark for Document Forgery Detection and Analysis*, arXiv.
