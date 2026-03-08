from __future__ import annotations

from ..schemas import DatasetSpec

DATASET_CATALOG = [
    DatasetSpec(
        slug="doctamper",
        name="DocTamper",
        task_focus="Localisation de falsification textuelle dans des documents.",
        public_status="Code public ; accès dataset encadré selon le dépôt.",
        recommended_use="Pré-entraînement ou benchmark de localisation.",
        notes="Benchmark central pour la littérature DTD / FFDN.",
    ),
    DatasetSpec(
        slug="find_it_again",
        name="Find it Again!",
        task_focus="Fraude réaliste sur tickets de caisse.",
        public_status="Public.",
        recommended_use="Validation terrain sur reçus falsifiés.",
        notes="988 tickets dont 163 modifiés frauduleusement.",
    ),
    DatasetSpec(
        slug="cord",
        name="CORD",
        task_focus="Structure de tickets et parsing post-OCR.",
        public_status="Public via dépôt / miroirs.",
        recommended_use="Préparer gabarits et sections de tickets.",
        notes="Reçus indonésiens annotés pour OCR et parsing.",
    ),
    DatasetSpec(
        slug="xfund",
        name="XFUND",
        task_focus="Formulaires multilingues structurés.",
        public_status="Public.",
        recommended_use="Tester l'analyse de champs et de structure.",
        notes="7 langues avec annotations clé-valeur.",
    ),
]
