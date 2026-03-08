from docfraud_layout import AnalysisConfig, analyze_document


def test_sample_doc_triggers_expected_categories():
    report = analyze_document(AnalysisConfig(document_path="examples/sample_doc.json"))
    categories = {anomaly.categorie for anomaly in report.anomalies}
    assert report.type_document == "facture"
    assert "champ_mal_positionne" in categories
    assert "police_non_standard" in categories or "police_rare" in categories
    assert report.score_layout <= 100.0
    assert report.nb_elements_ocr > 0
