# Références scientifiques

## Références centrales

1. Qu, C. et al. (CVPR 2023). *Towards Robust Tampered Text Detection in Document Image: New Dataset and New Solution*.  
   DTD introduit un modèle combinant domaine visuel et coefficients DCT, ainsi que le dataset DocTamper à 170k images.

2. Chen, Z. et al. (ECCV 2024). *Enhancing Tampered Text Detection through Frequency Feature Fusion and Decomposition*.  
   FFDN renforce l'intérêt des indices fréquentiels et évalue explicitement DocTamper et T-SROIE.

3. Wang, Q. et al. (ACL 2025). *Innovative Image Fraud Detection with Cross-Sample Anomaly Analysis: The Power of LLMs*.  
   CSIAD montre que le LLM est surtout utile pour une analyse logique cross-sample, pas comme juge visuel unique.

4. Wu, J. et al. (arXiv 2026). *AIForge-Doc: A Benchmark for Detecting AI-Forged Tampering in Financial and Form Documents*.  
   Benchmark centré sur l'inpainting génératif de champs numériques, avec 4,061 faux documents sur CORD, WildReceipt, SROIE et XFUND.

5. Zhao, Z. et al. (arXiv 2026). *DOCFORGE-BENCH: A Comprehensive Benchmark for Document Forgery Detection and Analysis*.  
   Montre que la calibration est un verrou central pour la détection documentaire out-of-the-box.

## Références datasets

6. Find it Again! (ICDAR 2023). Dataset de 988 tickets, dont 163 modifiés frauduleusement.
7. CORD. Dataset de reçus structurés pour le parsing post-OCR.
8. XFUND. Dataset multilingue de formulaires annotés.

## Usage dans ce projet

- DTD / FFDN : justification des signaux visuels + fréquentiels.
- CSIAD : positionnement de la couche explicative et de la revue humaine.
- AIForge-Doc : justification du focus sur les champs numériques et les faux modernes.
- DOCFORGE-BENCH : justification de la calibration au lieu d'un seuil fixe universel.
