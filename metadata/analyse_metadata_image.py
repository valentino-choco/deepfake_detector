import os
import re
import io
import struct
from PIL import Image, ImageChops, ImageEnhance
import piexif
from datetime import datetime

################################################################################################
# Listes de détection
################################################################################################

LOGICIELS_SUSPECTS = [
    'photoshop', 'illustrator', 'indesign', 'gimp', 'inkscape', 'paint',
    'ilovepdf', 'smallpdf', 'pdf2go', 'foxyutils', 'sodapdf', 'sejda', 'pdf candy',
    'canva', 'editor', 'foxit phantom', 'nitro pro', 'able2extract', 'icecream pdf',
    'nuance power pdf', 'phantompdf', 'skia/pdf', 'chromium','pypdf', 'reportlab', 
    'fpdf', 'skia', 'wkhtmltopdf', 'python', 'draw', 'pixlr', 'lightroom', 'snapseed',
    'picsart'
]

LOGICIELS_SURS = [
    'ricoh', 'canon', 'xerox', 'hp', 'hewlett-packard', 'lexmark', 
    'scansnap', 'epson', 'konica', 'kyocera', 'brother', 'sharp',
    'fujitsu', 'konicaminolta', 'samsung', 'oki'
]

ACTIONS_XMP_SUSPECTES = [
    b'converted', b'saved', b'cropped', b'paint', b'preview', 
    b'thumbnail', b'exported', b'created'
]

SEUIL_DONNEES_TRAINANTES = 1024 

################################################################################################
# Fonctions utilitaires (Identiques au PDF)
################################################################################################

def ajouter_alerte(resultats, titre, description, niveau):
    message = f"[{niveau}] {titre} : {description}"
    if niveau == "HAUT":
        resultats["alertes"].append(message)
        resultats["nb_alarmes"] += 1
    else :
        resultats["avertissements"].append(message)

def ajouter_validation(resultats, titre, description):
    resultats["validations"].append(f"[OK] {titre} : {description}")

def ajouter_info(resultats, titre, description):
    resultats["infos"].append(f"[INFO] {titre} : {description}")

def nettoyer_texte(chaine):
    if not chaine: return ""
    if isinstance(chaine, bytes):
        chaine = chaine.decode('utf-8', errors='ignore')
    return chaine.replace('\x00', '').strip()

################################################################################################
# Logique d'Analyse
################################################################################################

def analyser_image(chemin_fichier):
    resultats = {
        "alertes": [],
        "avertissements": [],
        "validations": [],
        "infos": [],
        "nb_alarmes": 0
    }

    if not os.path.exists(chemin_fichier):
        ajouter_alerte(resultats, "Fichier introuvable", f"Le fichier '{chemin_fichier}' n'existe pas.", "HAUT")
        return resultats

    try:
        # 1. LECTURE BINAIRE
        with open(chemin_fichier, 'rb') as f:
            donnees_binaires = f.read()
        
        taille_totale = len(donnees_binaires)
        extension = os.path.splitext(chemin_fichier)[1].lower()
        donnees_minuscules = donnees_binaires.lower()

        # 2. VÉRIFICATION DES MAGIC BYTES (Anti-usurpation)
        SIGNATURES_FORMATS = {
            '.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff',
            '.png': b'\x89PNG\r\n\x1a\n',
            '.gif': b'GIF8',
            '.bmp': b'BM',
            '.tiff': (b'II\x2a\x00', b'MM\x00\x2a'), '.tif': (b'II\x2a\x00', b'MM\x00\x2a'),
            '.webp': b'RIFF',
            '.heic': b'ftypheic', '.heif': b'ftypheif'
        }

        header_valide = False
        sig = SIGNATURES_FORMATS.get(extension)
        if sig:
            if isinstance(sig, tuple): header_valide = any(donnees_binaires.startswith(s) for s in sig)
            elif extension == '.webp': header_valide = donnees_binaires.startswith(b'RIFF') and b'WEBP' in donnees_binaires[8:12]
            elif extension in ['.heic', '.heif']: header_valide = b'ftyp' in donnees_binaires[4:12]
            else: header_valide = donnees_binaires.startswith(sig)

        if not header_valide:
            ajouter_alerte(resultats, "Format Invalide", f"La signature réelle ne correspond pas à l'extension {extension}.", "CRITIQUE")

        # 3. ANALYSE XMP & HISTORIQUE (Scan binaire profond)
        if b'xmp' in donnees_minuscules:
            trouvailles = [a.decode() for a in ACTIONS_XMP_SUSPECTES if a in donnees_minuscules]
            if trouvailles:
                ajouter_alerte(resultats, "Historique XMP", f"Traces de modifications trouvées dans le flux binaire : {', '.join(trouvailles)}", "MOYEN")

        # 4. OUVERTURE PILLOW & EXIF
        img = Image.open(chemin_fichier)
        fmt = img.format
        ajouter_info(resultats, "Format", f"{fmt} | Dimensions: {img.size}")

        soft_str = ""
        exif_raw = img.info.get("exif")
        if exif_raw:
            try:
                exif_dict = piexif.load(exif_raw)
                soft = exif_dict.get("0th", {}).get(piexif.ImageIFD.Software)
                if soft:
                    soft_str = nettoyer_texte(soft).lower()
                    ajouter_info(resultats, "Logiciel (EXIF)", soft_str)
                    if any(s in soft_str for s in LOGICIELS_SUSPECTS):
                        ajouter_alerte(resultats, "Logiciel Suspect", f"Détecté dans EXIF : {soft_str}", "HAUT")
            except: pass

        # 5. ANALYSE DQT (JPEG Uniquement)
        if fmt in ['JPEG', 'MPO']:
            SIGNATURES_DQT = {
                b'\x01\x01\x01\x01\x01\x01\x01\x01': "Qualité Maximale (Édition/IA)",
                b'\x02\x01\x01\x02\x01\x01\x02\x02': "Windows / Paint / Snipping Tool",
                b'\x03\x02\x02\x03\x02\x02\x03\x03': "Standard IJG (GIMP / Export Web)",
                b'\x06\x04\x04\x06\x04\x04\x05\x05': "Adobe Photoshop / Lightroom",
                b'\x08\x06\x06\x07\x06\x05\x08\x07': "Librairie de base (Pillow / OpenCV / WhatsApp)",
            }
            logiciel_dqt = next((nom for sig, nom in SIGNATURES_DQT.items() if sig in donnees_binaires), None)
            if logiciel_dqt:
                ajouter_info(resultats, "Signature DQT", f"Profil détecté : {logiciel_dqt}")
                if soft_str and "adobe" not in soft_str and "photoshop" in logiciel_dqt.lower():
                    ajouter_alerte(resultats, "Incohérence Structurelle", "L'EXIF prétend une source originale, mais la compression est celle de Photoshop.", "CRITIQUE")
                elif "Photoshop" in logiciel_dqt:
                    ajouter_alerte(resultats, "Signature DQT", "Table de quantification Adobe Photoshop détectée.", "HAUT")

        # 6. DÉTERMINATION DE LA FIN RÉELLE (Trailing Data)
        fin_attendue = taille_totale
        if fmt == 'JPEG':
            pos = donnees_binaires.rfind(b'\xff\xd9')
            if pos != -1: fin_attendue = pos + 2
        elif fmt == 'PNG':
            pos = donnees_binaires.rfind(b'IEND')
            if pos != -1: fin_attendue = pos + 8
        elif fmt == 'GIF':
            pos = donnees_binaires.rfind(b'\x3b')
            if pos != -1: fin_attendue = pos + 1
        elif fmt == 'BMP' and len(donnees_binaires) > 6:
            fin_attendue = int.from_bytes(donnees_binaires[2:6], 'little')
        elif fmt == 'WEBP' and len(donnees_binaires) > 8:
            fin_attendue = int.from_bytes(donnees_binaires[4:8], 'little') + 8
        elif fmt in ['HEIC', 'HEIF']:
            offset = 0
            while offset + 4 <= taille_totale:
                box_size = int.from_bytes(donnees_binaires[offset:offset+4], 'big')
                if box_size <= 0: break
                offset += box_size
            fin_attendue = offset

        # 7. ALERTES STRUCTURELLES
        trainee = taille_totale - fin_attendue
        if trainee > SEUIL_DONNEES_TRAINANTES:
            ajouter_alerte(resultats, "Données Traînantes", f"{trainee} octets suspects après la fin de l'image.", "HAUT")
        elif trainee < 0:
            ajouter_alerte(resultats, "Fichier Tronqué", "Le fichier est incomplet (données manquantes).", "MOYEN")

        # 8. ANALYSE ELA (JPEG)
        if fmt == 'JPEG':
            try:
                original = img.convert('RGB')
                tmp = io.BytesIO()
                original.save(tmp, 'JPEG', quality=90)
                tmp.seek(0)
                recompresse = Image.open(tmp)
                ela_im = ImageChops.difference(original, recompresse)
                max_diff = max([ex[1] for ex in ela_im.getextrema()])
                if max_diff > 35:
                    ajouter_alerte(resultats, "ELA", f"Score ELA élevé ({max_diff}). Possibilité de retouche locale.", "MOYEN")
            except: pass

    except Exception as e:
        ajouter_alerte(resultats, "Erreur Système", f"Échec de l'analyse : {str(e)}", "HAUT")

    return resultats

################################################################################################
# Affichage
################################################################################################

def afficher_rapport_image(chemin_image):
    ROUGE = '\033[91m'
    VERT  = '\033[92m'
    JAUNE = '\033[93m'
    RESET = '\033[0m'

    resultats = analyser_image(chemin_image)
    nom_fichier = os.path.basename(chemin_image)

    print("-" * 60)
    print(f"ANALYSE IMAGE : {nom_fichier}")
    print("-" * 60)

    if resultats["alertes"]:
        print(f"{ROUGE}ALERTES (HAUT) :{RESET}")
        for msg in resultats["alertes"]: print(f"  - {msg}")

    if resultats["avertissements"]:
        print(f"{JAUNE}AVERTISSEMENTS (MOYEN) :{RESET}")
        for msg in resultats["avertissements"]: print(f"  - {msg}")

    if resultats["validations"]:
        print(f"{VERT}VALIDATIONS :{RESET}")
        for msg in resultats["validations"]: print(f"  - {msg}")

    if resultats["infos"]:
        print("INFOS :")
        for msg in resultats["infos"]: print(f"  - {msg}")

    print("") 
    nb_alarmes = resultats.get('nb_alarmes', 0)
    if nb_alarmes > 0:
        print(f"--> CONCLUSION : {ROUGE}IMAGE SUSPECTE ({nb_alarmes} alertes critiques){RESET}")
    else:
        print(f"--> CONCLUSION : {VERT}IMAGE SAINE (PROBABLE){RESET}")
    print("\n")
