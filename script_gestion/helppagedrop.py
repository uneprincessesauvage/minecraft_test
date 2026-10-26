from mcrcon import MCRcon
from pathlib import Path

RCON_HOST = "127.0.0.1"
RCON_PORT = 25567
RCON_PASSWORD = "49a9854589a717628d5c326e"

NOMBRE_PAGES = 76

fichier = Path("./minecraft-help.txt")

with MCRcon(
    RCON_HOST,
    RCON_PASSWORD,
    port=RCON_PORT
) as rcon:

    with fichier.open("w", encoding="utf-8") as sortie:
        for page in range(1, NOMBRE_PAGES + 1):
            print(f"Récupération de la page {page}/{NOMBRE_PAGES}...")

            try:
                resultat = rcon.command(f"? {page}")

                sortie.write(f"\n{'=' * 60}\n")
                sortie.write(f"PAGE {page}\n")
                sortie.write(f"{'=' * 60}\n")
                sortie.write(resultat + "\n")

            except Exception as erreur:
                sortie.write(f"Erreur page {page} : {erreur}\n")

print(f"\nTerminé ! Résultats enregistrés dans : {fichier}")
