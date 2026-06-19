#!/usr/bin/env python3
"""
Met à jour le dateModified (JSON-LD) des pages HTML qui viennent
d'être réellement modifiées dans le commit, et synchronise le
lastmod correspondant dans sitemap.xml.

Ne touche à AUCUNE page non modifiée : la date reste honnête.
"""
import json
import re
import subprocess
import sys
from datetime import date

TODAY = date.today().isoformat()
SITE = "https://www.3hconseils.com/"


def changed_html_files():
    """Liste des .html modifiés dans le dernier commit (vs commit précédent)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            text=True,
        )
    except subprocess.CalledProcessError:
        # Premier commit du repo : rien à comparer, on ne touche à rien.
        return []
    files = [f for f in out.splitlines() if f.endswith(".html")]
    return files


def update_datemodified(path):
    """Met à jour dateModified dans le(s) bloc(s) JSON-LD WebPage/Article du fichier."""
    try:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
    except FileNotFoundError:
        return False  # fichier supprimé dans ce commit

    changed = False

    def repl(match):
        nonlocal changed
        block = match.group(1)
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            return match.group(0)
        targets = obj if isinstance(obj, list) else obj.get("@graph", [obj])
        touched = False
        for node in targets:
            if isinstance(node, dict) and node.get("@type") in ("WebPage", "Article"):
                if "dateModified" in node:
                    node["dateModified"] = TODAY
                    touched = True
        if not touched:
            return match.group(0)
        changed = True
        new_block = json.dumps(obj, ensure_ascii=False, indent=2)
        return f"<script type=\"application/ld+json\">\n{new_block}\n  </script>"

    new_src = re.sub(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        repl,
        src,
        flags=re.S,
    )

    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_src)
    return changed


def update_sitemap(updated_pages):
    """Met à jour lastmod pour les URL correspondant aux pages modifiées."""
    try:
        with open("sitemap.xml", encoding="utf-8") as fh:
            sm = fh.read()
    except FileNotFoundError:
        return False

    changed = False
    for page in updated_pages:
        url = SITE if page == "index.html" else SITE + page
        # Cherche le bloc <url>...<loc>URL</loc>...<lastmod>...</lastmod>...</url>
        pattern = re.compile(
            r"(<url>\s*<loc>" + re.escape(url) + r"</loc>.*?<lastmod>)(.*?)(</lastmod>)",
            re.S,
        )
        new_sm, n = pattern.subn(lambda m: m.group(1) + TODAY + m.group(3), sm)
        if n:
            sm = new_sm
            changed = True

    if changed:
        with open("sitemap.xml", "w", encoding="utf-8") as fh:
            fh.write(sm)
    return changed


def main():
    files = changed_html_files()
    # On ignore les pages techniques qui n'ont pas vocation à être datées
    files = [f for f in files if f not in ("404.html", "page-merci.html", "page-capture.html")]

    if not files:
        print("Aucune page HTML modifiée dans ce commit : rien à dater.")
        return

    updated = []
    for f in files:
        if update_datemodified(f):
            updated.append(f)
            print(f"dateModified mis à jour : {f}")
        else:
            print(f"(pas de bloc dateModified à mettre à jour dans {f})")

    if updated:
        if update_sitemap(updated):
            print("sitemap.xml : lastmod synchronisé pour les pages modifiées.")
        else:
            print("sitemap.xml : aucune URL correspondante trouvée (vérifier les chemins).")
    else:
        print("Rien à committer : aucune date n'a changé.")
        sys.exit(0)


if __name__ == "__main__":
    main()
