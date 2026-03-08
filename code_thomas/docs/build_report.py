from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
OUT = DOCS / "rapport_final_layout_fraud.pdf"
ANALYSIS_JSON = ROOT / "analysis_report.json"


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.1 * cm, f"Page {doc.page}")
    canvas.restoreState()


def p(text, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def img(path: Path, width_cm: float, caption: str, styles):
    probe = Image(str(path))
    ratio = probe.imageHeight / max(1, probe.imageWidth)
    target_width = width_cm * cm
    target_height = target_width * ratio
    image = Image(str(path), width=target_width, height=target_height)
    return [image, Spacer(1, 0.15 * cm), Paragraph(caption, styles["Caption"]), Spacer(1, 0.35 * cm)]


def build():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, leading=24, textColor=colors.HexColor("#1f3b63")))
    styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], fontSize=16, leading=20, textColor=colors.HexColor("#1f3b63"), spaceAfter=8))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#244b7a"), spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=10.2, leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="Caption", parent=styles["Italic"], fontSize=9, leading=11, textColor=colors.HexColor("#555555"), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=4))
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Rapport final — détection de fraudes documentaires par analyse de mise en page",
        author="OpenAI",
    )

    story = []
    story += [
        Spacer(1, 2.0 * cm),
        Paragraph("Rapport final — détection de fraudes documentaires par analyse de mise en page", styles["TitleCenter"]),
        Spacer(1, 0.4 * cm),
        Paragraph("Version fidèle au notebook initial, restructurée en projet Python lisible, testable et documenté.", styles["Caption"]),
        Spacer(1, 0.8 * cm),
        Paragraph(
            "Ce rapport décrit la démarche complète de réimplémentation des analyses de mise en page demandées : "
            "structure de référence, ordre des sections, alignement, logos, en-têtes/pieds de page, champs inattendus et polices non standard.",
            styles["Body"],
        ),
        Spacer(1, 0.4 * cm),
    ]
    story += img(ASSETS / "pipeline_diagram.png", 15.5, "Figure 1 — Architecture finale du pipeline.", styles)

    story += [
        Paragraph("1. Contexte et objectif", styles["H1"]),
        Paragraph(
            "Le notebook d'origine contenait déjà plusieurs analyses pertinentes de fraude documentaire, mais leur migration vers les versions intermédiaires du projet avait partiellement perdu des briques importantes de mise en page. "
            "Le but de ce livrable final est de réimplémenter explicitement ces analyses dans un package Python modulaire sans sacrifier la lisibilité pour les relecteurs.",
            styles["Body"],
        ),
        Paragraph(
            "Le périmètre demandé était précis : comparer la mise en page à une structure de référence, vérifier les sections et champs obligatoires, détecter les incohérences d'alignement, les décalages de logos, les incohérences d'en-tête/pied de page, les champs à des emplacements inattendus et les polices non standard.",
            styles["Body"],
        ),
        Paragraph("2. Diagnostic de l'existant", styles["H1"]),
        Paragraph(
            "Le notebook d'origine implémentait déjà des fonctions dédiées à ces besoins, notamment `_analyze_sections`, `_analyze_alignments`, `analyze_field_positions`, `analyze_header_footer_consistency`, "
            "`analyze_font_consistency_per_zone`, `detect_graphic_zones`, `analyze_multipage_consistency` et `analyze_pdf_fonts`. Une partie de ces fonctions n'était plus pleinement branchée dans le pipeline final précédent.",
            styles["Body"],
        ),
        Paragraph(
            "La stratégie retenue a donc consisté à repartir de ces fonctions comme source de vérité, puis à les transformer en modules séparés, documentés et testables.",
            styles["Body"],
        ),
        Paragraph("3. Correspondance exacte avec les remarques de départ", styles["H1"]),
    ]
    story += img(ASSETS / "requirement_mapping.png", 16.0, "Figure 2 — Correspondance entre les remarques initiales et les modules finaux.", styles)

    story += [
        Paragraph("4. Réimplémentation détaillée", styles["H1"]),
        Paragraph("4.1 Structure de référence", styles["H2"]),
        Paragraph(
            "Le fichier `reference_data.py` centralise les gabarits documentaires. Pour chaque type (facture, relevé bancaire, contrat, ticket), il définit les sections attendues, leurs zones Y normalisées, les mots-clés associés et la zone attendue du logo. "
            "Le module `layout_reference.py` exploite ensuite ces gabarits pour mesurer la couverture, signaler les sections obligatoires absentes et contrôler l'ordre vertical des sections observées.",
            styles["Body"],
        ),
        Paragraph("4.2 Champs mal positionnés", styles["H2"]),
        Paragraph(
            "Toujours dans `layout_reference.py`, la fonction `analyze_field_positions` compare des mots-clés forts comme `IBAN`, `SIRET`, `TOTAL`, `DATE` ou `SIGNATURE` à des bandes verticales attendues. "
            "Cette brique répond directement à la remarque sur les champs de texte à des emplacements inattendus.",
            styles["Body"],
        ),
        Paragraph("4.3 Alignement et espacement", styles["H2"]),
        Paragraph(
            "Le module `layout_alignment.py` reconstruit des colonnes dominantes à partir des positions `x_min`, mesure les désalignements globaux et par section, puis ajoute une analyse des interlignes irréguliers. "
            "Ces signaux doivent être lus comme des indices de revue et non comme une preuve autonome ; ils sont néanmoins très utiles pour localiser des collages ou des insertions textuelles.",
            styles["Body"],
        ),
        Paragraph("4.4 Polices non standard", styles["H2"]),
        Paragraph(
            "Le module `font_analysis.py` couvre trois niveaux : (i) dispersion globale des hauteurs de texte, (ii) cohérence des tailles par section, (iii) analyse des familles de polices rares ou inhabituelles, aussi bien au niveau des éléments OCR qu'au niveau des polices embarquées dans un PDF natif. "
            "Cela répond à la remarque sur l'usage de polices non standard.",
            styles["Body"],
        ),
        Paragraph("4.5 Logos et cohérence header/footer", styles["H2"]),
        Paragraph(
            "Le module `visual_layout.py` compare visuellement l'en-tête, le corps et le pied de page à partir de la variance du Laplacien et d'une mesure ELA simple. Il détecte aussi des zones graphiques par densité de gradient et vérifie si un logo attendu est absent, décalé ou flou.",
            styles["Body"],
        ),
        Paragraph("4.6 Cohérence multi-pages", styles["H2"]),
        Paragraph(
            "Le module `multipage.py` ajoute deux contrôles : la cohérence visuelle inter-pages et la stabilité des signatures textuelles d'en-tête/pied de page. Il mesure aussi la dispersion horizontale des zones graphiques d'en-tête pour repérer un logo qui change de place au fil du document.",
            styles["Body"],
        ),
    ]

    story += [
        Paragraph("5. Positionnement scientifique", styles["H1"]),
        Paragraph(
            "Le projet est volontairement interprétable, mais il s'appuie sur des constats récents de la littérature. DTD / DocTamper propose une approche visuelle + DCT et un dataset de 170 000 images, ce qui a imposé l'idée que les indices fréquentiels restent cruciaux pour les faux textuels documentaires. "
            "FFDN prolonge cette intuition en améliorant la fusion fréquentielle sur DocTamper et T-SROIE. CSIAD montre ensuite que les LLM sont particulièrement utiles pour détecter des contradictions logiques entre documents proches, plutôt que comme simples juges visuels globaux.",
            styles["Body"],
        ),
        Paragraph(
            "Plus récemment, AIForge-Doc décrit un benchmark centré sur l'inpainting génératif de champs numériques : 4 061 faux documents produits à partir de CORD, WildReceipt, SROIE et XFUND, avec des masques pixel précis. "
            "DOCFORGE-BENCH montre de son côté que le verrou pratique n'est pas seulement la représentation, mais aussi la calibration : des méthodes peuvent conserver un bon AUC tout en ayant un F1 presque nul si le seuil n'est pas adapté au domaine.",
            styles["Body"],
        ),
    ]
    story += img(ASSETS / "scientific_timeline.png", 15.2, "Figure 3 — Repères scientifiques mobilisés.", styles)
    story += img(ASSETS / "scoring_calibration.png", 14.0, "Figure 4 — Concept de calibration du score final.", styles)

    story += [
        Paragraph("6. Exemple de sortie sur le document d'exemple", styles["H1"]),
    ]

    if ANALYSIS_JSON.exists():
        payload = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))
        summary_table = Table(
            [
                ["Type document", payload.get("type_document", "")],
                ["Source", payload.get("source_kind", "")],
                ["Pages", str(payload.get("nb_pages", ""))],
                ["Éléments OCR", str(payload.get("nb_elements_ocr", ""))],
                ["Score brut", str(payload.get("score_layout_raw", ""))],
                ["Score calibré", str(payload.get("score_layout", ""))],
                ["Sections manquantes", ", ".join(payload.get("sections_manquantes", [])) or "aucune"],
            ],
            colWidths=[5.3 * cm, 9.7 * cm],
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("BOX", (0,0), (-1,-1), 0.8, colors.grey),
            ("INNERGRID", (0,0), (-1,-1), 0.4, colors.lightgrey),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("PADDING", (0,0), (-1,-1), 6),
        ]))
        story += [summary_table, Spacer(1, 0.4 * cm)]
        anomalies = payload.get("anomalies", [])[:7]
        if anomalies:
            rows = [["Catégorie", "Sévérité", "Impact", "Description"]]
            for item in anomalies:
                rows.append([
                    item.get("categorie", ""),
                    item.get("severite", ""),
                    str(item.get("score_impact", "")),
                    item.get("description", "")[:95],
                ])
            table = Table(rows, colWidths=[3.1 * cm, 2.1 * cm, 1.4 * cm, 9.0 * cm], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eaf0f8")),
                ("BOX", (0,0), (-1,-1), 0.8, colors.grey),
                ("INNERGRID", (0,0), (-1,-1), 0.4, colors.lightgrey),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE", (0,0), (-1,-1), 9),
                ("LEADING", (0,0), (-1,-1), 11),
                ("PADDING", (0,0), (-1,-1), 5),
            ]))
            story += [table, Spacer(1, 0.35 * cm)]

    story += [
        Paragraph("7. Tests et reproductibilité", styles["H1"]),
        Paragraph(
            "Le dépôt contient un test `pytest`, un script d'analyse CLI, un script de benchmark simple et un notebook de démonstration. Les figures du rapport sont générées par des scripts Python dédiés dans `docs/figure_code/`. "
            "Ce choix garantit que le rapport peut être régénéré et audité, au même titre que le code métier.",
            styles["Body"],
        ),
        Paragraph("8. Limites et suites possibles", styles["H1"]),
        Paragraph(
            "Le projet reste essentiellement heuristique et interprétable. Il ne remplace pas un modèle appris de localisation ni une calibration fondée sur un vrai jeu de validation terrain. "
            "La prochaine extension naturelle serait d'ajouter un segmentateur RGB + DCT inspiré de DTD / FFDN, puis d'utiliser ce pipeline de mise en page comme couche d'explication et de revue humaine.",
            styles["Body"],
        ),
        Paragraph("9. Références", styles["H1"]),
    ]

    bibliography = [
        "[R1] Qu, C. et al. (2023). Towards Robust Tampered Text Detection in Document Image: New Dataset and New Solution. CVPR.",
        "[R2] Chen, Z. et al. (2024). Enhancing Tampered Text Detection through Frequency Feature Fusion and Decomposition. ECCV.",
        "[R3] Wang, Q. et al. (2025). Innovative Image Fraud Detection with Cross-Sample Anomaly Analysis: The Power of LLMs. ACL.",
        "[R4] Wu, J. et al. (2026). AIForge-Doc: A Benchmark for Detecting AI-Forged Tampering in Financial and Form Documents. arXiv:2602.20569.",
        "[R5] Zhao, Z. et al. (2026). DOCFORGE-BENCH: A Comprehensive Benchmark for Document Forgery Detection and Analysis. arXiv:2603.01433.",
        "[R6] Tornés, B. M. et al. (2023). Receipt Dataset for Document Forgery Detection. ICDAR Workshops.",
        "[R7] CORD repository and associated receipt parsing dataset.",
        "[R8] XFUND: A Multilingual Form Understanding Benchmark.",
    ]
    for item in bibliography:
        story.append(Paragraph(item, styles["Small"]))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build()
