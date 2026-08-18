#!/usr/bin/env python3
"""
Générateur de slides de story Instagram 3H Conseils — version harmonisée.

Corrige les deux problèmes identifiés par Hugues (03/08/2026) :
1. Polices différentes selon les slides -> une seule famille (Playfair Display)
   sur tous les templates, jouée en Bold/Regular/Italic selon la hiérarchie.
2. Format carré (1080x1080) qui laissait des bandes noires en story -> format
   plein cadre story (1080x1920).

Palette de marque (charte v4.0) :
    Noir  #111111
    Crème #F5F0E8
    Doré  #A5915C

Usage :
    python3 generate_story_slide.py --type citation --text "..." --out out/1-citation.png
    python3 generate_story_slide.py --type temoignage --text "..." --auteur "M. D." --out out/3-temoignage.png
    python3 generate_story_slide.py --type definition --titre "..." --text "..." --out out/4-definition.png
    python3 generate_story_slide.py --type cta --text "..." --out out/5-cta.png

Produit un PNG 1080x1920 prêt à être poussé dans
assets/social/stories/{jour}/ sur le dépôt GitHub hugueshippler-bit/3hconseils-site-V2.
"""

import argparse
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NOIR = (17, 17, 17)
CREME = (245, 240, 232)
DORE = (165, 145, 92)

# Le script cherche les fontes Playfair Display dans ./fonts (à côté de ce
# script) ou dans /home/claude/fonts. Récupérez les fichiers .ttf depuis
# https://fonts.google.com/specimen/Playfair+Display et déposez-les dans un
# dossier "fonts" au même niveau que ce script si besoin.
FONT_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
    "/home/claude/fonts",
    "/mnt/skills/public/docx/fonts",
]

FONT_FILES = {
    "regular": "PlayfairDisplay-Regular.ttf",
    "bold": "PlayfairDisplay-Bold.ttf",
    "italic": "PlayfairDisplay-Italic.ttf",
}


def _find_font_dir():
    for d in FONT_CANDIDATES:
        if os.path.isdir(d) and any(
            os.path.isfile(os.path.join(d, f)) for f in FONT_FILES.values()
        ):
            return d
    return None


def font(size, weight="regular"):
    """Charge Playfair Display si disponible, sinon retombe sur une police
    système pour ne jamais bloquer la génération."""
    d = _find_font_dir()
    if d:
        path = os.path.join(d, FONT_FILES.get(weight, FONT_FILES["regular"]))
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    # Fallback : police système (le rendu ne sera pas identique à Playfair
    # Display tant que les .ttf ne sont pas fournis, mais le script ne
    # plante pas et le format/la mise en page restent corrects).
    for fallback in ["DejaVuSerif-Bold.ttf", "DejaVuSerif.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_frame(draw):
    """Cadre doré fin, cohérent sur tous les slides (marge de 48px, trait 3px)."""
    margin = 48
    draw.rectangle(
        [margin, margin, W - margin, H - margin],
        outline=DORE,
        width=3,
    )


def draw_logo(draw, color=DORE):
    """Logo texte '3H CONSEILS' sobre, centré en haut."""
    f = font(34, "bold")
    text = "3H CONSEILS"
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, 110), text, font=f, fill=color)


def wrap_and_draw(draw, text, f, y_center, max_width_px, fill, line_spacing=1.35):
    """Centre un bloc de texte multi-lignes verticalement autour de y_center."""
    # Estimation du nombre de caractères par ligne à partir de la taille de fonte
    avg_char_w = f.getlength("n") or (f.size * 0.55)
    chars_per_line = max(10, int(max_width_px / avg_char_w))
    lines = textwrap.wrap(text, width=chars_per_line)

    line_height = f.size * line_spacing
    total_h = line_height * len(lines)
    y = y_center - total_h / 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw) / 2, y), line, font=f, fill=fill)
        y += line_height


def base_canvas():
    img = Image.new("RGB", (W, H), NOIR)
    draw = ImageDraw.Draw(img)
    draw_frame(draw)
    draw_logo(draw)
    return img, draw


def slide_citation(text, auteur=None, out="out/1-citation.png"):
    img, draw = base_canvas()
    f_quote = font(58, "italic")
    f_auteur = font(30, "regular")
    wrap_and_draw(draw, f"« {text} »", f_quote, H / 2, W - 220, CREME)
    if auteur:
        f = f_auteur
        bbox = draw.textbbox((0, 0), f"— {auteur}", font=f)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, H / 2 + 220), f"— {auteur}", font=f, fill=DORE)
    _save(img, out)


def slide_temoignage(text, auteur=None, out="out/3-temoignage.png"):
    img, draw = base_canvas()
    f_label = font(30, "bold")
    label = "TÉMOIGNAGE"
    bbox = draw.textbbox((0, 0), label, font=f_label)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 320), label, font=f_label, fill=DORE)

    f_quote = font(48, "italic")
    wrap_and_draw(draw, f"« {text} »", f_quote, H / 2, W - 220, CREME)

    if auteur:
        f = font(28, "regular")
        bbox = draw.textbbox((0, 0), auteur, font=f)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, H / 2 + 260), auteur, font=f, fill=DORE)
    _save(img, out)


def slide_definition(titre, text, out="out/4-definition.png"):
    img, draw = base_canvas()
    f_titre = font(46, "bold")
    bbox = draw.textbbox((0, 0), titre, font=f_titre)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 260), titre, font=f_titre, fill=DORE)

    f_def = font(38, "regular")
    wrap_and_draw(draw, text, f_def, H / 2 + 60, W - 220, CREME)
    _save(img, out)


def slide_cta(text, sous_texte="3hconseils.com", out="out/5-cta.png"):
    img, draw = base_canvas()
    f_cta = font(52, "bold")
    wrap_and_draw(draw, text, f_cta, H / 2 - 40, W - 220, CREME)

    f_sous = font(30, "italic")
    bbox = draw.textbbox((0, 0), sous_texte, font=f_sous)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 + 180), sous_texte, font=f_sous, fill=DORE)
    _save(img, out)


def _save(img, out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, "PNG")
    print(f"Généré : {out} ({W}x{H})")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--type", required=True, choices=["citation", "temoignage", "definition", "cta"])
    p.add_argument("--text", required=True)
    p.add_argument("--titre", default=None, help="Requis pour --type definition")
    p.add_argument("--auteur", default=None, help="Optionnel pour citation/temoignage")
    p.add_argument("--sous-texte", default="3hconseils.com", help="Optionnel pour cta")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    if args.type == "citation":
        slide_citation(args.text, args.auteur, args.out or "out/1-citation.png")
    elif args.type == "temoignage":
        slide_temoignage(args.text, args.auteur, args.out or "out/3-temoignage.png")
    elif args.type == "definition":
        if not args.titre:
            p.error("--titre est requis pour --type definition")
        slide_definition(args.titre, args.text, args.out or "out/4-definition.png")
    elif args.type == "cta":
        slide_cta(args.text, args.sous_texte, args.out or "out/5-cta.png")


if __name__ == "__main__":
    main()
