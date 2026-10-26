from mcrcon import MCRcon
from pathlib import Path
import re
RCON_HOST = "127.0.0.1"
RCON_PORT = 25567
RCON_PASSWORD = "49a9854589a717628d5c326e"
fichier = Path("./minecraft-gamerules.txt")
def nettoyer_minecraft(texte):
    return re.sub(r"§[0-9a-fk-or]", "", texte, flags=re.IGNORECASE)
def nombre_pages(texte):
    match = re.search(r"\[Page\s+1\s+of\s+(\d+)\]", texte)
    return int(match.group(1)) if match else 1
with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as rcon:
    with fichier.open("w", encoding="utf-8") as sortie:
        # Récupération de la liste des mondes
        resultat = nettoyer_minecraft(
            rcon.command("mv list --page 1")
        )
        pages_mondes = nombre_pages(resultat)
        mondes = []
        for page in range(1, pages_mondes + 1):
            resultat = nettoyer_minecraft(
                rcon.command(f"mv list --page {page}")
            )
            for ligne in resultat.splitlines():
                match = re.search(
                    r"^\s*(.+?)\s+-\s+(NORMAL|NETHER|THE_END)\s*$",
                    ligne
                )
                if match:
                    mondes.append(match.group(1).strip())
        # Suppression des doublons en conservant l'ordre
        mondes = list(dict.fromkeys(mondes))
        # Récupération des gamerules de chaque monde
        for monde in mondes:
            print(f"Récupération des gamerules : {monde}")
            try:
                resultat = nettoyer_minecraft(
                    rcon.command(f"mv gamerule list {monde}")
                )
                total_pages = nombre_pages(resultat)
                sortie.write("\n" + "=" * 60 + "\n")
                sortie.write(f"MONDE : {monde}\n")
                sortie.write("=" * 60 + "\n")
                sortie.write(resultat + "\n")
                # Récupération des pages suivantes
                for page in range(2, total_pages + 1):
                    resultat = nettoyer_minecraft(
                        rcon.command(
                            f"mv gamerule list {monde} --page {page}"
                        )
                    )
                    sortie.write("\n" + resultat + "\n")
            except Exception as erreur:
                sortie.write(
                    f"\nErreur pour le monde {monde} : {erreur}\n"
                )
print(f"\nTerminé ! Résultats enregistrés dans : {fichier.resolve()}")
