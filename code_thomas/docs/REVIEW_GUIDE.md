# Guide de relecture

## 1. Ce qu'il faut vérifier en premier

- `src/docfraud_layout/reference_data.py` : gabarits de structure et zones attendues.
- `src/docfraud_layout/layout_reference.py` : sections, ordre, champs mal positionnés.
- `src/docfraud_layout/layout_alignment.py` : colonnes dominantes, désalignements, espacement.
- `src/docfraud_layout/font_analysis.py` : polices globales, par zone, PDF.
- `src/docfraud_layout/visual_layout.py` : header/footer, logos, densité d'encre.
- `src/docfraud_layout/multipage.py` : cohérence entre pages.
- `src/docfraud_layout/pipeline.py` : orchestration globale.

## 2. Correspondance avec les remarques initiales

### Remarque 1 — comparer la mise en page à une structure de référence
Implémentation :
- `reference_data.py`
- `layout_reference.analyze_reference_sections`

### Remarque 2 — ordre des sections et champs obligatoires
Implémentation :
- `layout_reference.analyze_reference_sections`

### Remarque 3 — incohérences d'alignement
Implémentation :
- `layout_alignment.analyze_alignment_consistency`
- `layout_alignment.analyze_spacing_consistency`

### Remarque 4 — décalage dans les logos
Implémentation :
- `visual_layout.detect_graphic_zones`
- `multipage.analyze_multipage_consistency`

### Remarque 5 — incohérence des en-têtes/pieds de page
Implémentation :
- `visual_layout.analyze_header_footer_consistency`
- `multipage.analyze_multipage_consistency`

### Remarque 6 — champs de texte à des emplacements inattendus
Implémentation :
- `layout_reference.analyze_field_positions`

### Remarque 7 — polices non standard
Implémentation :
- `font_analysis.analyze_element_font_usage`
- `font_analysis.analyze_pdf_fonts`
- `font_analysis.analyze_font_consistency_per_zone`
