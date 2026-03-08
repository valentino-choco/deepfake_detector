from __future__ import annotations

import argparse
from pathlib import Path

from docfraud_layout import AnalysisConfig, analyze_document
from docfraud_layout.reporting import report_to_console, write_json_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse un document pour la fraude documentaire.")
    parser.add_argument("--document", required=True, help="Chemin vers le document (.pdf, .json, .png...)")
    parser.add_argument("--doc-type", default=None, help="Type documentaire forcé")
    parser.add_argument("--output", default=None, help="Chemin de sortie JSON")
    args = parser.parse_args()

    config = AnalysisConfig(document_path=args.document, doc_type_override=args.doc_type)
    report = analyze_document(config)
    print(report_to_console(report))
    if args.output:
        write_json_report(report, args.output)
        print(f"\nRapport JSON écrit dans {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
