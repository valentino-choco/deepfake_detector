from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (900, 1250), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 220, 140), fill=(30, 70, 140))
    draw.rectangle((620, 40, 850, 140), outline=(180, 180, 180), width=2)
    draw.text((60, 70), "ACME", fill="white")
    draw.text((640, 70), "FACTURE", fill="black")
    y = 190
    for line in [
        "Client : Example Client",
        "Date : 12/02/2026",
        "Facture n : FAC-2026-0008",
        "Description          Qté     PU       Total",
        "Ordinateur           1       1299.99  1299.99",
        "Garantie             1        199.99   199.99",
        "Total HT                                1499.98",
        "TVA                                      300.00",
        "Total TTC                                1799.98",
        "IBAN FR76 3000 4000 5000 6000 7000 890",
    ]:
        draw.text((60, y), line, fill="black")
        y += 70
    draw.text((60, 1180), "Conditions de règlement sous 30 jours", fill=(80, 80, 80))
    image.save(out_dir / "sample_invoice.png")
    image.save(out_dir / "sample_invoice.pdf")


if __name__ == "__main__":
    main()
