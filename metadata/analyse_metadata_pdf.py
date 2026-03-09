import os
import re
import sys
import io
from datetime import datetime
from pypdf import PdfReader

################################################################################################
# Liste des logificels
################################################################################################

# Listes de détection
LOGICIELS_SUSPECTS = [
    'photoshop', 'illustrator', 'indesign', 'gimp', 'inkscape', 'paint',
    'ilovepdf', 'smallpdf', 'pdf2go', 'foxyutils', 'sodapdf', 'sejda', 'pdf candy',
    'canva', 'editor', 'foxit phantom', 'nitro pro', 'able2extract', 'icecream pdf',
    'nuance power pdf', 'phantompdf', 'skia/pdf', 'chromium','pypdf', 'reportlab', 
    'fpdf', 'skia', 'wkhtmltopdf', 'python', 'draw', 'pixlr', 'lightroom', 'snapseed',
    'picsart'
]

LOGICIELS_AMBIGUS = [
    'conversion plug-in', 'microsoft print to pdf', 'pdfium', 
    'quartz pdf context', 'acrobat distiller', 'pscript5.dll', 'mozilla',
    'word', 'powerpoint', 'libreoffice', 'writer', 'openoffice', 'pages',
]

LOGICIELS_SURS = [
    'ricoh', 'canon', 'xerox', 'hp', 'hewlett-packard', 'lexmark', 
    'scansnap', 'epson', 'konica', 'kyocera', 'brother', 'sharp',
    'fujitsu', 'konicaminolta', 'samsung', 'oki',
    'docuware', 'papyrus', 'windev', 'sap', 'crystal reports', 
    'afp', 'crawfordtech', 'opentext', 'ibm', 'streamserve',
    'businessobjects', 'jasperreports', 'itext', 'fpdf', 'tcpdf'
]

ACTIONS_XMP_SUSPECTES = ['derived', 'converted', 'saved', 'cropped', 'retouched']
SEUIL_DONNEES_TRAINANTES = 1024 

################################################################################################
# Fonctions utiles
################################################################################################

def ajouter_alerte(resultats, titre, description, niveau):
    message = f"[{niveau}] {titre} : {description}"
    if niveau == "HAUT":
        resultats["alertes"].append(message)
        resultats["nb_alarmes"] += 1
    else :
        resultats["avertissements"].append(message)
    return

def ajouter_validation(resultats, titre, description):
    resultats["validations"].append(f"[OK] {titre} : {description}")

def ajouter_info(resultats, titre, description):
    resultats["infos"].append(f"[INFO] {titre} : {description}")

def verifier_chaine(chaine_brute, nom_champ, resultats):
    anomalies = []
    if not chaine_brute:
        anomalies.append('Champ vide')
    # Null Bytes
    if '\x00' in chaine_brute:
        anomalies.append("Null Byte (\\x00)")
    
    # Espaces Insécables
    if '\xa0' in chaine_brute:
        anomalies.append("Espace Insécable (\\xa0)")
        
    # Tabulations
    if '\t' in chaine_brute:
        anomalies.append("Tabulation (\\t)")

    if anomalies:
        description = f"Caractères suspects dans '{nom_champ}' : {', '.join(anomalies)}."
        niveau = "HAUT" if "Null Byte" in description else "MOYEN"
        ajouter_alerte(resultats, "Anomalie d'encodage", description, niveau)

def nettoyer_texte(chaine):
    if not chaine:
        return " "
    return chaine.replace('\x00', '').replace('\xa0', ' ').replace('\t', ' ').strip()

def convertir_date_pdf(date_val):
    if not date_val:
        return None
    # Si pypdf a déjà converti en datetime
    if isinstance(date_val, datetime):
        return date_val.replace(tzinfo=None) # On ignore le fuseau pour comparer
    try:
        # Nettoyage plus large pour les chaînes
        propre = re.sub(r'[^0-9]', '', str(date_val)) # On ne garde que les chiffres
        if len(propre) >= 14:
            return datetime.strptime(propre[:14], "%Y%m%d%H%M%S")
        elif len(propre) >= 8:
            return datetime.strptime(propre[:8], "%Y%m%d")
    except:
        return None
    return None

################################################################################################
# Analyse
################################################################################################

def analyser_pdf(chemin_fichier):
    resultats = {
            "alertes": [],
            "avertissements": [],
            "validations": [],
            "infos" : [],
            "nb_alarmes": 0
    }

    if not os.path.exists(chemin_fichier):
        ajouter_alerte(resultats, "Fichier introuvable", f"Le fichier '{chemin_fichier}' n'existe pas.", "HAUT")
        return resultats

    print(f"Analyse en cours de : {os.path.basename(chemin_fichier)}...")

    # Extraction des métadonnées PDF
    try:
        with open(chemin_fichier, "rb") as f:
            contenu_binaire = f.read()

        flux_memoire = io.BytesIO(contenu_binaire)
        reader = PdfReader(flux_memoire)
        meta = reader.metadata
        texte_brut = contenu_binaire.decode('latin-1', errors='ignore')

    except Exception as e:
        ajouter_alerte(resultats, "Erreur de lecture", f"Impossible de lire le fichier PDF : {str(e)}", "HAUT")
        return resultats
    

    if not meta:
        ajouter_alerte(resultats, "Métadonnées absentes", "Le fichier PDF ne contient pas de métadonnées.", "MOYEN")
        return resultats
    else :
        ajouter_info(resultats, "Métadonnées trouvées", "Le fichier PDF contient des métadonnées.")
        infos_soft = ""
        flag_producer = False
        flag_creator = False
        if meta.creator :
            flag_creator = True
            raw_creator = meta.creator if meta.creator else ""
            if raw_creator:
                verifier_chaine(raw_creator, "Creator", resultats)
                createur = nettoyer_texte(raw_creator)
                ajouter_info(resultats, "Logiciel Créateur", createur)
                infos_soft += createur.lower()
        if meta.producer :
            flag_producer = True
            raw_producer = meta.producer if meta.producer else ""
            if raw_producer:
                verifier_chaine(raw_producer, "Producer", resultats)
                producteur = nettoyer_texte(raw_producer)
                ajouter_info(resultats, "Logiciel Producteur", producteur)
                if infos_soft == "":
                    infos_soft += producteur.lower()
                else :
                    infos_soft += " " + producteur.lower()
        if infos_soft == "":
            ajouter_alerte(resultats, "Informations logicielles manquantes", "Les champs Creator et Producer sont absents ou incomplets.", "MOYEN" )

        date_creation = None
        date_modif = None
        
        if meta.creation_date:
            date_creation = convertir_date_pdf(meta.creation_date)
            if date_creation:
                ajouter_info(resultats, "Date de création", f"Le document a été créé le {date_creation.strftime('%d/%m/%Y %H:%M:%S')}.")
        
        if meta.modification_date:
            date_modif = convertir_date_pdf(meta.modification_date)
            if date_modif:
                ajouter_info(resultats, "Date de modification", f"Le document a été modifié le {date_modif.strftime('%d/%m/%Y %H:%M:%S')}.")    

        # Vérifier les deux dates converties, pas les métadonnées brutes
        if date_modif and date_creation:
            if date_modif == date_creation:
                ajouter_alerte(resultats, "Incohérence de dates", "La date de modification est identique à la date de création. (enregistrement automatisé suspect)", "MOYEN")
            if date_modif < date_creation:
                ajouter_alerte(resultats, "Incohérence de dates", "La date de modification est antérieure à la date de création.", "MOYEN")

        

    # Analyse structure
    marqueurs_eof = [m.start() for m in re.finditer(b'%%EOF', contenu_binaire)]
    nb_eof = len(marqueurs_eof)

    if nb_eof == 0:
        ajouter_alerte(resultats, "Marqueur EOF manquant", "Le fichier PDF ne contient pas de marqueur de fin '%%EOF'. Le fichier peut être corrompu.", "HAUT")
    elif nb_eof > 1:
        ajouter_alerte(resultats, "Multiples marqueurs EOF", f"Le fichier PDF contient {nb_eof} marqueurs de fin '%%EOF'. Il a pu être modifié après création.", "MOYEN")

    if nb_eof > 0:
        fin = contenu_binaire[marqueurs_eof[-1]+5:].strip()
        if len(fin) > SEUIL_DONNEES_TRAINANTES:
            ajouter_alerte(resultats, "Données Traînantes", f"{len(fin)} octets suspects à la fin.", "HAUT")

    # Analyse des métadonnées
    found_soft = False
    if infos_soft:
        for soft in LOGICIELS_SUSPECTS:
            if soft in infos_soft:
                ajouter_alerte(resultats, "Logiciel Suspect Détecté", f"Le logiciel '{soft}' a été détecté dans les métadonnées.", "HAUT")
                found_soft = True
        if not found_soft:
            for soft in LOGICIELS_AMBIGUS:
                if soft in infos_soft:
                    ajouter_alerte(resultats, "Logiciel Ambigu Détecté", f"Le logiciel '{soft}' a été détecté dans les métadonnées.", "MOYEN")
                    found_soft = True
        if not found_soft:
            for soft in LOGICIELS_SURS:
                if soft in infos_soft:
                    ajouter_validation(resultats, "Logiciel professionnel detecté", f"Le logiciel '{soft}' a été détecté dans les métadonnées.")
                    found_soft = True
        if not found_soft:
            ajouter_info(resultats, "Aucun logiciel connu détecté", "Aucun logiciel suspect, n'a été détecté dans les métadonnées.")

    # Analyse XMP
    has_xmp = '<x:xmpmeta' in texte_brut.lower()
    if not has_xmp:
        ajouter_alerte(resultats, "Métadonnées XMP absentes", "Le fichier PDF ne contient pas de métadonnées XMP.", "MOYEN")
    else :
        xmp = reader.xmp_metadata
        if xmp:
            flag_creator_xmp = False
            xmp_creator = (xmp.xmp_creator_tool or "").lower()
            xmp_creator = nettoyer_texte(xmp_creator)
            if xmp_creator != "":
                flag_creator_xmp = True

            flag_producer_xmp = False
            xmp_producer = (xmp.pdf_producer or "").lower()
            xmp_producer = nettoyer_texte(xmp_producer)
            if xmp_producer != "":
                flag_producer_xmp = True


            if flag_creator and flag_creator_xmp :
                if (createur not in xmp_creator) and (xmp_creator not in createur):
                    ajouter_alerte(resultats, "Incohérence Créateur XMP", f"La valeur Creator Tool XMP ('{xmp_creator}') diffère du champ Creator PDF ('{createur}').", "MOYEN")
            elif not flag_producer and flag_producer_xmp :
                ajouter_info(resultats, "Producteur XMP sans équivalent PDF", f"Le champ Producer PDF est vide alors que le champ Producer XMP contient : '{xmp_producer}'.")
            elif not flag_creator and not flag_creator_xmp :
                ajouter_info(resultats, "Créateur absent des deux métadonnées", "Le champ Creator est vide à la fois dans les métadonnées PDF et XMP.")

            if producteur and xmp_producer :
                if (producteur not in xmp_producer) and (xmp_producer not in producteur):
                    ajouter_alerte(resultats, "Incohérence Producteur XMP", f"La valeur Producer XMP ('{xmp_producer}') diffère du champ Producer PDF ('{producteur}').", "MOYEN")
            elif not flag_producer and flag_producer_xmp :
                ajouter_info(resultats, "Producteur XMP sans équivalent PDF", f"Le champ Producer PDF est vide alors que le champ Producer XMP contient : '{xmp_producer}'.")   
            elif not flag_producer and not flag_producer_xmp :
                ajouter_info(resultats, "Producteur absent des deux métadonnées", "Le champ Producer est vide à la fois dans les métadonnées PDF et XMP.")

            xmp_date_obj = xmp.xmp_create_date
            if xmp_date_obj and date_creation:
                try:
                    xmp_date = convertir_date_pdf(xmp_date_obj.isoformat())
                    diff = abs((xmp_date - date_creation).total_seconds())
                    if diff > 60: 
                        ajouter_alerte(resultats, "Incohérence Date Création XMP", "Différence > 1 min entre XMP et Meta", "MOYEN")
                except: pass

        try:
            debut = texte_brut.lower().find('<x:xmpmeta')
            fin = texte_brut.lower().find('</x:xmpmeta>')
            
            if debut != -1 and fin != -1:
                # +20 pour inclure la balise de fin
                bloc_xmp_str = texte_brut[debut:fin+20].lower()
                
                for action in ACTIONS_XMP_SUSPECTES:
                    if action in bloc_xmp_str:
                        ajouter_alerte(resultats, "Trace d'édition (XMP)", f"Action suspecte trouvée dans l'historique XMP : '{action}'.", "MOYEN")
        except Exception as e:
            pass

        for soft in LOGICIELS_SUSPECTS:
            if soft in texte_brut.lower() and soft not in infos_soft:
                ajouter_alerte(resultats, "Trace Cachée (XMP)", f"Logiciel '{soft}' masqué dans XMP.", "HAUT")

    return resultats

################################################################################################
# Analyse des listes de fichiers
################################################################################################

def afficher_rapport_pdf(chemin_pdf):
    if not os.path.exists(chemin_pdf):
        print(f"Erreur : Le fichier '{chemin_pdf}' est introuvable.")
        return

    ROUGE = '\033[91m'
    VERT  = '\033[92m'
    JAUNE = '\033[93m'
    RESET = '\033[0m'

    resultats = analyser_pdf(chemin_pdf)
    if not resultats:
        print(f"{ROUGE}Erreur d'analyse pour {os.path.basename(chemin_pdf)}{RESET}")
        return

    nom_fichier = os.path.basename(chemin_pdf)
    print("-" * 60)
    print(f"ANALYSE : {nom_fichier}")
    print("-" * 60)

    if resultats.get("alertes"):
        print(f"{ROUGE}ALERTES :{RESET}")
        for msg in resultats["alertes"]:
            print(f"  - {msg}")

    if resultats.get("avertissements"):
        print(f"{JAUNE}AVERTISSEMENTS :{RESET}")
        for msg in resultats["avertissements"]:
            print(f"  - {msg}")

    if resultats.get("validations"):
        print(f"{VERT}VALIDATIONS :{RESET}")
        for msg in resultats["validations"]:
            print(f"  - {msg}")

    if resultats.get("infos"):
        print("INFOS :")
        for msg in resultats["infos"]:
            print(f"  - {msg}")

    # 5. Conclusion
    print("") 
    nb_alarmes = resultats.get('nb_alarmes', 0)
    if nb_alarmes > 0:
        print(f"--> CONCLUSION : {ROUGE}SUSPECT ({nb_alarmes} alertes){RESET}")
    else:
        print(f"--> CONCLUSION : {VERT}OK{RESET}")
    print("\n")