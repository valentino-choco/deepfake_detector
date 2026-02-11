import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import re
import json
import numpy as np
import cv2
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from docling.document_converter import DocumentConverter

# --- INITIALISATION (Une seule fois pour pas ramer) ---
# On charge PaddleOCR ici pour l'avoir sous le coude
ocr = PaddleOCR(use_angle_cls=True, lang='fr')
converter = DocumentConverter()

def clean_amt(text):
    if not text: return 0.0
    # On vire les symboles monétaires et on gère la virgule
    clean = re.sub(r'[^\d,\.]', '', str(text)).replace(',', '.')
    try:
        return float(clean)
    except:
        return 0.0

def process_document(pdf_path):
    filename = os.path.basename(pdf_path)
    print(f"--- Analyse du document : {filename} ---")
    
    # 1. TENTATIVE RAPIDE AVEC DOCLING (PDF Numérique)
    result = converter.convert(pdf_path)
    doc_text = result.document.export_to_markdown()
    
    # Si Docling ne renvoie presque rien, c'est sûrement un scan, on passe à l'OCR
    if len(doc_text.strip()) < 50:
        print("C'est du scan, je sors la loupe (OCR)...")
        images = convert_from_path(pdf_path, dpi=200) # 200 DPI suffit pour la vitesse
        img_np = np.array(images[0])
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        
        ocr_res = ocr.ocr(img_bgr, cls=True)
        # On reconstruit les lignes (version simplifiée pour la vitesse)
        lines = []
        if ocr_res[0]:
            for line in ocr_res[0]:
                lines.append(line[1][0])
        doc_text = "\n".join(lines)

    print(doc_text)
    
    return structuration_finale(doc_text, filename)

def structuration_finale(raw_text, filename):
    # La carlingue du JSON que tu voulais
    res = {
        "titre": f"Document {filename}",
        "type": "Inconnu",
        "date": None,
        "client": None,
        "fournisseur": None,
        "reference": None,
        "contenu": []
    }

    lines = raw_text.split('\n')
    
    # Détection du type
    if any(x in raw_text.lower() for x in ['facture', 'invoice']):
        res["type"] = "facture"
    elif any(x in raw_text.lower() for x in ['relevé', 'compte']):
        res["type"] = "relevé de compte"

    # Extraction des infos de tête (Regex)
    date_match = re.search(r'\d{2}/\d{2}/\d{2,4}', raw_text)
    if date_match: res["date"] = date_match.group(0)
    
    ref_match = re.search(r'(?:N°|Ref|Facture)\s*[:\s]*([A-Z0-9\-_]+)', raw_text, re.I)
    if ref_match: res["reference"] = ref_match.group(1)

    # Extraction des lignes d'articles
    line_idx = 1
    for line in lines:
        # On cherche des lignes avec au moins un prix (ex: 125,50)
        prices = re.findall(r'\d+[\s,.]\d{2}', line)
        if len(prices) >= 1:
            # On essaie d'isoler le libellé
            label = line
            for p in prices: label = label.replace(p, "")
            label = re.sub(r'[|#*]', '', label).strip()
            
            if len(label) > 3: # Éviter les lignes vides
                res["contenu"].append({
                    "ligne": line_idx,
                    "libellé": label[:60],
                    "quantité": 1, # Par défaut
                    "prix_unitaire": clean_amt(prices[0]),
                    "prix": clean_amt(prices[-1])
                })
                line_idx += 1

    return res

# --- LE TEST GADJO ---
if __name__ == "__main__":
    mon_pdf = "data/facture3.pdf" # Mets ton chemin ici
    if os.path.exists(mon_pdf):
        resultat_json = process_document(mon_pdf)
        
        # Affichage propre
        print("\n--- CONTENU STRUCTURÉ ---")
        print(json.dumps(resultat_json, indent=4, ensure_ascii=False))
        
        # Sauvegarde
        with open('resultat_final.json', 'w', encoding='utf-8') as f:
            json.dump(resultat_json, f, ensure_ascii=False, indent=4)
    else:
        print("Le fichier existe pas, t'essaies de m'entuber ?")