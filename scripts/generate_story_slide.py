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
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NOIR = (17, 17, 17)
CREME = (245, 240, 232)
DORE = (165, 145, 92)


def typo_fr(s):
    """Applique les règles de typographie française :
    - apostrophe typographique (') au lieu de l'apostrophe droite (')
    - nombre et % collés (90% et non 90 %)
    - espace insécable avant ; : ! ?
    Appliqué systématiquement à tout texte affiché, pour que la règle
    tienne sans avoir à y repenser à chaque nouveau texte."""
    if not s:
        return s
    s = s.replace("'", "\u2019")
    s = re.sub(r"(\d)\s?%", r"\1%", s)
    s = re.sub(r"\s*([;:!?])", "\u00A0" + r"\1", s)
    return s

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


LOGO_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "img", "logo-3hconseils-v2.png"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "img", "logo-3hconseils-v2.png"),
    "/home/claude/repo/assets/img/logo-3hconseils-v2.png",
]


def _find_logo():
    for p in LOGO_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def draw_logo(draw, img=None, color=DORE):
    """Insère le vrai logo 3H Conseils (monogramme HHH + baseline) si le
    fichier est disponible ; retombe sur un texte si le fichier est absent,
    pour ne jamais bloquer la génération."""
    logo_path = _find_logo()
    if img is not None and logo_path:
        logo = Image.open(logo_path).convert("RGBA")
        target_w = 460
        ratio = target_w / logo.width
        logo = logo.resize((target_w, int(logo.height * ratio)))
        x = (W - logo.width) // 2
        y = 90
        img.alpha_composite(logo, (x, y))
        return
    # Fallback texte si le logo n'est pas trouvé.
    f = font(40, "bold")
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


def draw_icon(draw, categorie):
    """Icône discrète sous le logo, propre à chaque catégorie de citation.
    Reste dans la palette dorée pour ne jamais casser l'harmonisation."""
    import math

    cx, cy = W / 2, 470

    if categorie == "sportif":
        # Petit rameau de laurier stylisé (deux arcs symétriques de tigelles).
        for side in (-1, 1):
            for i in range(6):
                angle = math.radians(90 + side * (18 + i * 11))
                x1 = cx + side * 10 + 22 * math.cos(angle)
                y1 = cy + 22 * math.sin(angle)
                x2 = cx + side * 10 + 40 * math.cos(angle)
                y2 = cy + 40 * math.sin(angle)
                draw.line([x1, y1, x2, y2], fill=DORE, width=3)
    elif categorie == "philosophe":
        # Petite colonne grecque (chapiteau, fût cannelé, base).
        draw.rectangle([cx - 32, cy - 22, cx + 32, cy - 15], fill=DORE)
        draw.rectangle([cx - 24, cy - 15, cx + 24, cy + 20], outline=DORE, width=3)
        for lx in range(-16, 17, 8):
            draw.line([cx + lx, cy - 15, cx + lx, cy + 20], fill=DORE, width=2)
        draw.rectangle([cx - 32, cy + 20, cx + 32, cy + 27], fill=DORE)
    elif categorie == "mecanisme":
        # Petite spirale (pensée en mouvement) plutôt qu'un cerveau figuratif.
        points = []
        for t in range(0, 640, 6):
            rad = math.radians(t)
            rr = 2 + t / 22
            points.append((cx + rr * math.cos(rad), cy + rr * math.sin(rad)))
        draw.line(points, fill=DORE, width=3)
    # categorie=None ou inconnue -> pas d'icône (témoignage, définition, cta)


def base_canvas(categorie=None):
    img = Image.new("RGBA", (W, H), (*NOIR, 255))
    draw = ImageDraw.Draw(img)
    draw_frame(draw)
    draw_logo(draw, img)
    if categorie:
        draw_icon(draw, categorie)
    return img, draw


def slide_citation(text, auteur=None, out="out/1-citation.png", categorie=None):
    text = typo_fr(text)
    auteur = typo_fr(auteur)
    img, draw = base_canvas(categorie)
    f_quote = font(58, "italic")
    f_auteur = font(36, "regular")
    wrap_and_draw(draw, f"«\u00A0{text}\u00A0»", f_quote, H / 2, W - 220, CREME)
    if auteur:
        f = f_auteur
        bbox = draw.textbbox((0, 0), f"— {auteur}", font=f)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, H / 2 + 220), f"— {auteur}", font=f, fill=DORE)
    _save(img, out)


def slide_temoignage(text, auteur=None, out="out/3-temoignage.png"):
    text = typo_fr(text)
    auteur = typo_fr(auteur)
    img, draw = base_canvas()
    f_label = font(30, "bold")
    label = "TÉMOIGNAGE"
    bbox = draw.textbbox((0, 0), label, font=f_label)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 320), label, font=f_label, fill=DORE)

    f_quote = font(48, "italic")
    wrap_and_draw(draw, f"«\u00A0{text}\u00A0»", f_quote, H / 2, W - 220, CREME)

    if auteur:
        f = font(36, "regular")
        bbox = draw.textbbox((0, 0), auteur, font=f)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2, H / 2 + 260), auteur, font=f, fill=DORE)
    _save(img, out)


def slide_definition(titre, text, out="out/4-definition.png"):
    titre = typo_fr(titre)
    text = typo_fr(text)
    img, draw = base_canvas()
    f_titre = font(46, "bold")
    bbox = draw.textbbox((0, 0), titre, font=f_titre)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H / 2 - 260), titre, font=f_titre, fill=DORE)

    f_def = font(38, "regular")
    wrap_and_draw(draw, text, f_def, H / 2 + 60, W - 220, CREME)
    _save(img, out)


def slide_cta(text, sous_texte="3hconseils.com", out="out/5-cta.png"):
    text = typo_fr(text)
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
    img.convert("RGB").save(out, "PNG")
    print(f"Généré : {out} ({W}x{H})")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--type", required=True, choices=["citation", "temoignage", "definition", "cta"])
    p.add_argument("--text", required=True)
    p.add_argument("--titre", default=None, help="Requis pour --type definition")
    p.add_argument("--auteur", default=None, help="Optionnel pour citation/temoignage")
    p.add_argument("--sous-texte", default="3hconseils.com", help="Optionnel pour cta")
    p.add_argument("--categorie", default=None, choices=["sportif", "philosophe", "mecanisme"],
                    help="Optionnel pour citation : ajoute une icône de catégorie")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    if args.type == "citation":
        slide_citation(args.text, args.auteur, args.out or "out/1-citation.png", args.categorie)
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
