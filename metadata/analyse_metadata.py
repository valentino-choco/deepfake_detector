from analyse_metadata_image import afficher_rapport_image
from analyse_metadata_pdf import afficher_rapport_pdf

fichier_test = r"C:\Liam data\PIE KPMG\Metadata\files\LIVE\0008 1 with photoshop.jpg"


if fichier_test.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp', '.heic', '.heif', '.raw')):
    afficher_rapport_image(fichier_test)
elif fichier_test.lower().endswith('.pdf'):
    afficher_rapport_pdf(fichier_test)