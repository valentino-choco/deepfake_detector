from __future__ import annotations

REFERENCE_LAYOUTS = {
    "facture": {
        "description": "Facture fournisseur ou prestataire",
        "champs_obligatoires": ["emetteur", "date", "numero_facture", "total_ttc"],
        "sections_attendues": [
            {"nom": "en_tete", "zone_y": (0.0, 0.18), "obligatoire": True},
            {"nom": "identifiants", "zone_y": (0.05, 0.32), "obligatoire": True},
            {"nom": "lignes", "zone_y": (0.25, 0.72), "obligatoire": True},
            {"nom": "totaux", "zone_y": (0.60, 0.92), "obligatoire": True},
            {"nom": "pied_de_page", "zone_y": (0.82, 1.00), "obligatoire": False},
        ],
        "keywords_sections": {
            "en_tete": ["facture", "invoice", "client", "fournisseur", "adresse"],
            "identifiants": ["date", "facture n", "invoice n", "commande", "référence"],
            "lignes": ["désignation", "quantité", "prix", "montant", "description"],
            "totaux": ["total", "ht", "tva", "ttc", "net à payer", "amount due"],
            "pied_de_page": ["iban", "bic", "conditions", "règlement", "paiement"],
        },
        "logo_zone": {"x": (0.0, 0.45), "y": (0.0, 0.18)},
    },
    "releve_bancaire": {
        "description": "Relevé bancaire",
        "champs_obligatoires": ["banque", "titulaire", "periode", "solde_fin"],
        "sections_attendues": [
            {"nom": "en_tete_banque", "zone_y": (0.0, 0.16), "obligatoire": True},
            {"nom": "info_compte", "zone_y": (0.08, 0.30), "obligatoire": True},
            {"nom": "transactions", "zone_y": (0.22, 0.84), "obligatoire": True},
            {"nom": "soldes", "zone_y": (0.74, 0.95), "obligatoire": True},
            {"nom": "pied_de_page", "zone_y": (0.90, 1.00), "obligatoire": False},
        ],
        "keywords_sections": {
            "en_tete_banque": ["banque", "agence", "crédit", "bnp", "cic", "lcl"],
            "info_compte": ["compte", "titulaire", "iban", "bic", "période", "relevé"],
            "transactions": ["date", "libellé", "débit", "crédit", "valeur", "opération"],
            "soldes": ["solde", "ancien", "nouveau", "solde de fin", "solde final"],
            "pied_de_page": ["conseiller", "téléphone", "réclamation"],
        },
        "logo_zone": {"x": (0.0, 0.45), "y": (0.0, 0.16)},
    },
    "contrat": {
        "description": "Contrat ou convention",
        "champs_obligatoires": ["titre", "parties", "signature"],
        "sections_attendues": [
            {"nom": "titre", "zone_y": (0.0, 0.12), "obligatoire": True},
            {"nom": "parties", "zone_y": (0.08, 0.30), "obligatoire": True},
            {"nom": "corps", "zone_y": (0.20, 0.82), "obligatoire": True},
            {"nom": "signatures", "zone_y": (0.76, 1.0), "obligatoire": True},
        ],
        "keywords_sections": {
            "titre": ["contrat", "convention", "accord", "objet"],
            "parties": ["entre", "société", "représenté", "siège", "partie"],
            "corps": ["article", "clause", "conditions", "durée", "paiement"],
            "signatures": ["fait à", "signature", "lu et approuvé", "bon pour accord"],
        },
        "logo_zone": {"x": (0.25, 0.75), "y": (0.0, 0.14)},
    },
    "ticket_caisse": {
        "description": "Ticket de caisse ou reçu",
        "champs_obligatoires": ["nom_etablissement", "date", "montant_ttc"],
        "sections_attendues": [
            {"nom": "en_tete", "zone_y": (0.0, 0.25), "obligatoire": True},
            {"nom": "identifiants", "zone_y": (0.05, 0.40), "obligatoire": True},
            {"nom": "articles", "zone_y": (0.20, 0.70), "obligatoire": True},
            {"nom": "totaux", "zone_y": (0.45, 0.85), "obligatoire": True},
            {"nom": "pied_ticket", "zone_y": (0.70, 1.0), "obligatoire": False},
        ],
        "keywords_sections": {
            "en_tete": ["restaurant", "café", "brasserie", "ticket", "bar", "hôtel"],
            "identifiants": ["siret", "tva", "tel", "date", "caisse", "ticket"],
            "articles": ["menu", "plat", "boisson", "café", "dessert", "x"],
            "totaux": ["total", "ttc", "ht", "tva", "cb", "espèces", "règlement"],
            "pied_ticket": ["merci", "visite", "nf525", "top caisse"],
        },
        "logo_zone": {"x": (0.15, 0.85), "y": (0.0, 0.22)},
    },
}

FIELD_EXPECTED_ZONES = {
    "facture": {
        "iban": (0.72, 1.0),
        "bic": (0.72, 1.0),
        "siret": (0.72, 1.0),
        "siren": (0.72, 1.0),
        "total": (0.55, 0.95),
        "ttc": (0.55, 0.95),
        "facture": (0.0, 0.30),
        "invoice": (0.0, 0.30),
        "date": (0.0, 0.40),
    },
    "releve_bancaire": {
        "iban": (0.0, 0.32),
        "solde": (0.60, 1.0),
        "relevé": (0.0, 0.25),
        "banque": (0.0, 0.20),
    },
    "contrat": {
        "signature": (0.70, 1.0),
        "fait à": (0.68, 1.0),
        "contrat": (0.0, 0.20),
        "siret": (0.0, 0.35),
    },
    "ticket_caisse": {
        "total": (0.40, 0.95),
        "ttc": (0.40, 0.95),
        "cb": (0.50, 1.0),
        "merci": (0.60, 1.0),
        "siret": (0.05, 0.45),
    },
}
