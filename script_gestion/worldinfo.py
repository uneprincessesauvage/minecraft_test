from mcrcon import MCRcon
from pathlib import Path
import re
RCON_HOST = "127.0.0.1"
RCON_PORT = 25567
RCON_PASSWORD = "49a9854589a717628d5c326e"
FICHIER = Path("./minecraft-world-info.txt")
def nettoyer_minecraft(texte):
    return re.sub(r"§[0-9a-fk-or]", "", texte, flags=re.IGNORECASE)
def recuperer_pages(rcon, commande, motif_pages):
    """Récupère toutes les pages annoncées par une commande."""
    resultat = nettoyer_minecraft(rcon.command(commande))
    match = re.search(motif_pages, resultat, re.IGNORECASE)
    if not match:
        return [resultat]
    total_pages = int(match.group(2))
    pages = [resultat]
    for page in range(2, total_pages + 1):
        resultat = nettoyer_minecraft(
            rcon.command(f"{commande} --page {page}")
        )
        pages.append(resultat)
    return pages
with MCRcon(
    RCON_HOST,
    RCON_PASSWORD,
    port=RCON_PORT
) as rcon:
    print("Récupération de la liste des mondes...")
    pages_mondes = recuperer_pages(
        rcon,
        "mv list --page 1",
        r"\[Page\s+(\d+)\s+of\s+(\d+)\]"
    )
    noms_mondes = []
    for contenu in pages_mondes:
        for ligne in contenu.splitlines():
            match = re.match(r"^\s*(.*?)\s+-\s+(NORMAL|NETHER|THE_END)\s*$", ligne)
            if match:
                nom = match.group(1).strip()
                if nom not in noms_mondes:
                    noms_mondes.append(nom)
    print(f"{len(noms_mondes)} mondes trouvés.")
    with FICHIER.open("w", encoding="utf-8") as sortie:
        for index, monde in enumerate(noms_mondes, start=1):
            print(f"[{index}/{len(noms_mondes)}] Monde : {monde}")
            try:
                premiere_page = nettoyer_minecraft(
                    rcon.command(f"mv info {monde} --page 1")
                )
                match = re.search(
                    r"\[Page\s+(\d+)\s+of\s+(\d+)\]",
                    premiere_page,
                    re.IGNORECASE
                )
                total_pages = int(match.group(2)) if match else 1
                sortie.write("\n" + "=" * 70 + "\n")
                sortie.write(f"MONDE : {monde}\n")
                sortie.write("=" * 70 + "\n")
                sortie.write(premiere_page + "\n")
                for page in range(2, total_pages + 1):
                    resultat = nettoyer_minecraft(
                        rcon.command(f"mv info {monde} --page {page}")
                    )
                    sortie.write(f"\n--- PAGE {page}/{total_pages} ---\n")
                    sortie.write(resultat + "\n")
            except Exception as erreur:
                sortie.write(f"\nErreur pour le monde {monde} : {erreur}\n")
print(f"\nTerminé ! Résultats enregistrés dans : {FICHIER.resolve()}")
