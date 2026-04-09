# 🔍 Deepfake Detector — Détection de Documents Falsifiés par IA

> Projet PIE MSXS_NIA_01 — ISAE-SUPAERO × KPMG (2025–2026)

Ce dépôt contient les travaux réalisés dans le cadre d'un projet de R&D mené sur 7 mois en partenariat avec **KPMG**, visant à explorer la détection automatique de documents comptables et administratifs falsifiés (factures, relevés bancaires, contrats, notes de frais…), notamment ceux générés ou modifiés à l'aide d'outils d'IA générative.

---

## 📋 Contexte

La fraude documentaire évolue rapidement. Des outils comme ChatGPT, FraudGPT ou OnlyFake permettent aujourd'hui de produire des faux documents visuellement crédibles à moindre coût. Pour un cabinet d'audit comme KPMG, garantir l'authenticité des pièces justificatives est un impératif de crédibilité — comme l'a dramatiquement illustré le scandale Wirecard en 2020.

Ce projet explore une approche **multi-critères et explicable** pour aider les auditeurs à identifier les documents suspects, sans boîte noire.

---

## 🗂️ Structure du dépôt

```
deepfake_detector/
│
├── code_thomas/            # Pipeline principal de détection (layout, forensique, scoring)
├── code_valentino/         # Extraction de données par LLM (Mistral AI) + structuration JSON
├── manual_extraction/      # Scripts d'extraction OCR manuelle (approche sans LLM)
├── metadata/               # Analyse des métadonnées PDF et images (EXIF, XMP, traces logiciels)
├── numerical_analysis/     # Vérifications arithmétiques, loi de Benford, cohérence numérique
├── verif_signature/        # Modèle CNN de vérification de signatures (Keras/TensorFlow)
│
├── requirements.txt        # Dépendances Python
└── README.md
```

---

## 🧩 Critères de détection implémentés

Le projet s'appuie sur **11 critères** répartis en 3 familles :

### 📝 Contenu (sémantique / linguistique)

| Critère | Statut | Notes |
|---|---|---|
| Imitation d'écriture humaine | ❌ Non implémenté | Non pertinent pour les documents administratifs standardisés |
| Imitation de signature | ⚠️ Prototype | AUC 0.883, EER 19.4% — nécessite une base de données de référence |
| Cohérence des valeurs numériques | ✅ Implémenté | Loi de Benford, vérification arithmétique, cohérence des taux |
| Analyse statistique de la structure (perplexité) | ⚠️ Prototype | Fine-tuning CamemBERT — manque de données d'entraînement |
| Cohérence interne | ❌ Non implémenté | Complexité d'extraction des données structurées |
| Cohérence externe (SIRET, TVA, IBAN…) | ❌ Non implémenté | Priorité recommandée pour la suite |

### 🏗️ Structure (mise en page)

| Critère | Statut | Notes |
|---|---|---|
| Analyse de la mise en page | ✅ Implémenté | Comparaison à un gabarit de référence par type de document |
| Analyse des incohérences d'alignement | ✅ Implémenté | Analyse géométrique et typographique locale (3 niveaux) |

### 🔬 Forensique (technique / numérique)

| Critère | Statut | Notes |
|---|---|---|
| Analyse des métadonnées (PDF & images) | ✅ Implémenté | Traces de logiciels, incohérences XMP, ELA |
| Détection d'images générées par IA | ❌ Non implémenté | Recommandations d'architecture disponibles dans le rapport |

---

## ⚙️ Architecture du pipeline

```
Document PDF/Image
       │
       ▼
[Étape 1] Ingestion & structuration
  OCR → Mistral AI → JSON typé (facture, contrat, RIB...)
       │
       ▼
[Étape 2] Trois familles d'analyse (parallèles)
  ├── A. Analyse statistique du texte (CamemBERT / perplexité)
  ├── B. Analyse de mise en page (structure + forensique visuel + candidats numériques)
  └── C. Analyse forensique binaire (métadonnées, traces logiciels)
       │
       ▼
[Étape 3] Cohérences interne & externe
  Vérifications arithmétiques, calendaires, registres officiels (INSEE, VIES...)
       │
       ▼
[Étape 4] Scoring & rapport
  Score de risque 0–100 + rapport d'anomalies détaillé
```

Le module de mise en page (`docfraud_layout`) se décompose en **3 couches** :
- **Couche 1 — Structurelle** : gabarits de référence, sections attendues, positions des champs
- **Couche 2 — Visuelle & forensique** : ELA, variance du Laplacien, cohérence inter-pages
- **Couche 3 — Candidats numériques** : ciblage des champs montants/dates/références (les plus falsifiés)

---

## 🚀 Installation

```bash
git clone https://github.com/valentino-choco/deepfake_detector.git
cd deepfake_detector
pip install -r requirements.txt
```

### Prérequis

- Python 3.8+
- Une clé API **Mistral AI** (pour l'extraction LLM — module `code_valentino`)
- Tesseract OCR installé sur la machine (pour l'extraction manuelle)

### Variables d'environnement

```bash
export MISTRAL_API_KEY="votre_clé_api"
```

---

## 📦 Modules — Guide rapide

### Extraction de données (`code_valentino/`)
Prend un fichier PDF en entrée, détecte son type, et retourne un JSON structuré avec les champs clés (dates, montants, SIRET, parties…).

```python
from extractor import extractor
data = extractor("chemin/vers/document.pdf")
```

### Analyse de métadonnées (`metadata/`)
Détecte les traces de manipulation dans les fichiers PDF et images (Photoshop, GIMP, Canva, FPDF, incohérences XMP/EXIF, ELA).

```python
python metadata_pdf.py document.pdf
python metadata_image.py image.jpg
```

### Analyse numérique (`numerical_analysis/`)
Vérifie la cohérence arithmétique (HT + TVA = TTC), la loi de Benford, et les patterns d'identifiants (IBAN, SIRET, numéros de sécurité sociale).

### Vérification de signatures (`verif_signature/`)
Modèle CNN basé sur des triplets (Keras/TensorFlow). Entraîné sur des paires de signatures, évalue la distance euclidienne entre une signature soumise et un profil de référence.

> ⚠️ **Note** : EER de 19.4% — ce module est un prototype de recherche et n'est pas recommandé pour un usage en production sans une base de données de référence étoffée (min. 12 signatures par auteur).

### Pipeline principal (`code_thomas/`)
Orchestre les 3 couches d'analyse de mise en page et produit un score de risque calibré avec rapport d'anomalies.

---

## 📊 Résultats et performances

| Module | Résultat |
|---|---|
| Extraction LLM (Mistral) | ~1 min/document, fonctionne sur factures, contrats, RIB, relevés |
| Métadonnées | Détecte efficacement les traces Photoshop/Canva/FPDF |
| Vérification de signatures | AUC = 0.883 — prototype fonctionnel, EER = 19.4% |
| Analyse de mise en page | Détecte sections manquantes, champs mal positionnés, incohérences typographiques |

**Principale limite identifiée** : le manque de données labellisées (seule une cinquantaine de documents falsifiés fournis sous NDA). Les modules évitent donc le ML supervisé au profit de règles explicables et de seuils calibrés.

---

## 🔮 Recommandations & perspectives

1. **Données d'abord** : constituer un corpus annoté de documents authentiques et falsifiés représentatif des formats KPMG France
2. **Cohérence externe** : implémenter les vérifications SIRET/INSEE, TVA/VIES, IBAN — critère à fort potentiel
3. **Standards émergents** : explorer C2PA (provenance numérique) et SynthID (watermarking) pour les documents futurs
4. **Calibration par type** : définir des seuils distincts selon le type de document (facture, ticket de caisse, PDF natif vs scanné)

---

## 📚 Références clés

- DocTamper (CVPR 2023) — détection de texte falsifié dans les documents
- FFDN (ECCV 2024) — analyse fréquentielle pour la détection de falsification
- AIForge-Doc (arXiv 2026) — benchmark sur les champs numériques ciblés par IA
- DOCFORGE-BENCH (arXiv 2026) — calibration des seuils par domaine et type de document
- DetectGPT (ICML 2023) — détection de texte généré par IA via courbure de perplexité

---

## 👥 Équipe

Projet réalisé par des étudiants de l'**ISAE-SUPAERO** (filières SDD/Neuro-IA et MSXS) :

| Nom | Rôle |
|---|---|
| Tom Duquennoy | Chef de projet |
| Valentin Oncle | Extraction de données, architecture |
| Liam Ferrand | Analyse des métadonnées, état de l'art |
| Thomas Fayard | Pipeline principal, analyse de mise en page |
| Octave Claich | Extraction de données, analyse numérique |

**Client** : KPMG (Alexandre Deparis, Baptiste Dedieu, Camille Mouysset)  
**Coach projet** : Stéphane Pelletier  
**Référent école** : Florian Simatos

---

## 📄 Licence

Ce projet est un travail académique réalisé dans le cadre du PIE MSXS_NIA_01 (2025–2026). Le code est fourni à titre de prototype de recherche.
