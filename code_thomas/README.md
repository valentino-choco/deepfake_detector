# Projet final — Détection de fraudes documentaires par analyse de mise en page

Il intègre explicitement les analyses qui répondaient aux remarques suivantes :

- comparaison de la mise en page à une structure de référence ;
- contrôle de l'ordre des sections et des champs obligatoires ;
- détection des incohérences d'alignement ;
- détection des logos décalés ou absents ;
- détection d'en-têtes / pieds de page incohérents ;
- détection de champs de texte à des emplacements inattendus ;
- détection de polices non standard et de polices rares.

## Structure

```text
document_fraud_layout_final_release/
├── notebooks/
│   └── document_fraud_layout_final.ipynb
├── src/docfraud_layout/
│   ├── config.py
│   ├── schemas.py
│   ├── io.py
│   ├── reference_data.py
│   ├── layout_reference.py
│   ├── layout_alignment.py
│   ├── font_analysis.py
│   ├── visual_layout.py
│   ├── multipage.py
│   ├── candidates.py
│   ├── candidate_signals.py
│   ├── calibration.py
│   ├── scoring.py
│   ├── pipeline.py
│   └── reporting.py
├── scripts/
│   ├── run_analysis.py
│   ├── run_benchmark.py
│   └── make_example_assets.py
├── examples/
├── docs/
│   ├── rapport_final_layout_fraud.pdf
│   ├── SCIENTIFIC_REFERENCES.md
│   ├── REVIEW_GUIDE.md
│   ├── FINAL_ARCHITECTURE.md
│   ├── assets/
│   └── figure_code/
└── tests/
```

## Logique du pipeline

1. **Ingestion**
   - JSON OCR ;
   - PDF natif avec extraction des mots et des polices ;
   - image / PDF raster pour les analyses visuelles.

2. **Analyse de référence**
   - sections attendues ;
   - sections obligatoires ;
   - ordre observé des sections ;
   - champs sémantiques mal positionnés.

3. **Analyse géométrique**
   - colonnes dominantes ;
   - désalignements globaux et par section ;
   - irrégularités d'espacement.

4. **Analyse de polices**
   - variance globale des tailles ;
   - cohérence des tailles par zone ;
   - familles de polices rares ou non standard ;
   - familles de polices embarquées dans les PDF.

5. **Analyse visuelle**
   - cohérence header / body / footer ;
   - détection de zones graphiques ;
   - logos absents, flous ou décalés ;
   - densité d'encre locale.

6. **Analyse multi-pages**
   - cohérence inter-pages ;
   - cohérence des en-têtes et pieds de page ;
   - stabilité des zones graphiques entre pages.

7. **Analyse locale par candidats numériques**
   - montants, dates, longues références ;
   - signaux locaux interprétables ;
   - revue humaine ciblée.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Test rapide

```bash
python -m pytest -q
python scripts/run_analysis.py --document examples/sample_doc.json --output analysis_report.json
```

## Rapport

Le fichier `docs/rapport_final_layout_fraud.pdf` décrit :
- la démarche ;
- la correspondance exacte avec les remarques de départ ;
- les choix d'architecture ;
- les limites ;
- les références scientifiques ;
- les diagrammes produits dans `docs/figure_code/`.
