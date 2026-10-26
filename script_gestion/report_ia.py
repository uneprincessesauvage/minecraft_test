import json
import os
import re
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
import time

CONTAINER = "minecraft"
OUTPUT = Path("/data/myworld/script_minecraft/diagnostic-minecraft.txt")

# Variables autorisées dans le rapport.
# Les mots de passe et autres secrets sont exclus.
SAFE_ENV = [
    "TYPE", "VERSION", "PAPER_BUILD", "FORGE_VERSION",
    "FABRIC_LOADER_VERSION", "MEMORY", "JAVA_VERSION",
    "EULA", "ONLINE_MODE", "MAX_PLAYERS", "MOTD",
    "DIFFICULTY", "LEVEL", "LEVEL_TYPE", "PVP",
    "VIEW_DISTANCE", "SIMULATION_DISTANCE",
    "ENABLE_RCON", "RCON_PORT", "ENABLE_WHITELIST",
    "TZ", "UID", "GID"
]


def commande(args, timeout=10):
    try:
        p = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)


def titre(rapport, texte):
    rapport.extend(["", "=" * 65, texte, "=" * 65])


def nettoyer(texte):
    return str(texte).replace("\r", " ").strip()


def lire_metadonnees(jar):
    """Lit les métadonnées disponibles dans un fichier JAR."""
    resultat = {}

    try:
        with zipfile.ZipFile(jar) as archive:
            fichiers = archive.namelist()

            # Plugins Bukkit / Paper
            for nom in ("paper-plugin.yml", "plugin.yml"):
                if nom in fichiers:
                    contenu = archive.read(nom).decode(
                        "utf-8", errors="replace"
                    )

                    for cle in (
                        "name", "version", "main",
                        "api-version", "depend", "softdepend"
                    ):
                        match = re.search(
                            r"(?m)^" + cle + r"\s*:\s*(.*?)\s*$",
                            contenu
                        )
                        if match:
                            resultat[cle] = match.group(1).strip(
                                "'\" "
                            )
                    return resultat

            # Mods Fabric
            if "fabric.mod.json" in fichiers:
                data = json.loads(
                    archive.read("fabric.mod.json").decode("utf-8")
                )
                resultat["name"] = data.get("name", "")
                resultat["version"] = data.get("version", "")
                resultat["id"] = data.get("id", "")
                resultat["depend"] = ", ".join(
                    data.get("depends", {}).keys()
                )
                return resultat

            # Mods Forge
            if "META-INF/mods.toml" in fichiers:
                contenu = archive.read(
                    "META-INF/mods.toml"
                ).decode("utf-8", errors="replace")

                for cle in ("modId", "displayName", "version"):
                    match = re.search(
                        r'(?m)^\s*' + cle +
                        r'\s*=\s*["\']([^"\']+)["\']',
                        contenu
                    )
                    if match:
                        resultat[cle] = match.group(1)

                if resultat:
                    return resultat

    except Exception as e:
        resultat["erreur_lecture"] = type(e).__name__

    return resultat


def main():
    rapport = [
        "INVENTAIRE TECHNIQUE MINECRAFT",
        f"Date : {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Conteneur demandé : {CONTAINER}",
        "Aucun journal serveur n'est collecté.",
        "Les secrets ne doivent pas apparaître dans ce rapport."
    ]

    # --------------------------------------------------
    # 1. Docker
    # --------------------------------------------------
    code, sortie, erreur = commande(
        ["docker", "inspect", CONTAINER]
    )

    if code != 0:
        titre(rapport, "ERREUR DOCKER")
        rapport.append(erreur or sortie)
        enregistrer(rapport)
        return

    try:
        info = json.loads(sortie)[0]
    except (ValueError, IndexError):
        rapport.append("Impossible de lire les informations Docker.")
        enregistrer(rapport)
        return

    config = info.get("Config", {})
    etat = info.get("State", {})
    hote = info.get("HostConfig", {})
    env = {}

    for ligne in config.get("Env", []):
        if "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            env[cle] = valeur

    titre(rapport, "1. SERVEUR ET CONTENEUR")

    rapport.extend([
        f"Nom : {info.get('Name', '').lstrip('/')}",
        f"État : {etat.get('Status', 'inconnu')}",
        f"Image : {config.get('Image', 'inconnue')}",
        f"Création : {info.get('Created', 'inconnue')}",
        f"Démarrage : {etat.get('StartedAt', 'inconnu')}",
        f"Redémarrage automatique : "
        f"{hote.get('RestartPolicy', {}).get('Name', 'inconnu')}",
        f"Réseaux Docker : "
        f"{', '.join(info.get('NetworkSettings', {}).get('Networks', {}).keys()) or 'aucun'}"
    ])

    # --------------------------------------------------
    # 2. Configuration
    # --------------------------------------------------
    titre(rapport, "2. CONFIGURATION")

    for cle in SAFE_ENV:
        if cle in env:
            rapport.append(f"{cle} = {env[cle]}")

    # Ne jamais afficher les variables secrètes.
    rapport.append(
        "Variables sensibles : volontairement exclues."
    )

    # --------------------------------------------------
    # 3. Ports
    # --------------------------------------------------
    titre(rapport, "3. PORTS")

    ports = info.get("NetworkSettings", {}).get("Ports") or {}

    if ports:
        for port, liaisons in sorted(ports.items()):
            if liaisons:
                for liaison in liaisons:
                    rapport.append(
                        f"{liaison.get('HostIp', '0.0.0.0')}:"
                        f"{liaison.get('HostPort')} -> {port}"
                    )
            else:
                rapport.append(f"{port} : non publié sur l'hôte")
    else:
        rapport.append("Aucun port publié.")

    # --------------------------------------------------
    # 4. Volumes
    # --------------------------------------------------
    titre(rapport, "4. VOLUMES ET DOSSIERS")

    sources_data = []

    for volume in info.get("Mounts", []):
        source = volume.get("Source", "?")
        destination = volume.get("Destination", "?")

        rapport.append(
            f"{source} -> {destination} "
            f"(lecture seule : {not volume.get('RW', True)})"
        )

        if destination == "/data":
            sources_data.append(Path(source))

    if not info.get("Mounts"):
        rapport.append("Aucun volume monté.")

    # --------------------------------------------------
    # 5. Plugins et mods installés
    # --------------------------------------------------
    titre(rapport, "5. PLUGINS ET MODS INSTALLÉS")

    repertoires = []

    for source in sources_data:
        for dossier in ("plugins", "mods"):
            chemin = source / dossier
            if chemin.is_dir():
                repertoires.append(chemin)

    nombre = 0

    for dossier in sorted(set(repertoires)):
        fichiers = sorted(dossier.glob("*.jar"))

        rapport.append(
            f"\nDossier : {dossier} ({len(fichiers)} fichiers JAR)"
        )

        for jar in fichiers:
            nombre += 1
            meta = lire_metadonnees(jar)

            nom = (
                meta.get("name")
                or meta.get("displayName")
                or meta.get("id")
                or jar.stem
            )

            version = meta.get("version", "non détectée")

            rapport.append(f"- {nom} | version : {version}")
            rapport.append(f"  Fichier : {jar.name}")

            if meta.get("api-version"):
                rapport.append(
                    f"  API Minecraft : {meta['api-version']}"
                )

            if meta.get("depend"):
                rapport.append(
                    f"  Dépendances : {meta['depend']}"
                )

            if meta.get("softdepend"):
                rapport.append(
                    f"  Dépendances facultatives : {meta['softdepend']}"
                )

    if nombre == 0:
        rapport.append(
            "Aucun JAR trouvé dans les dossiers des volumes montés."
        )

    # --------------------------------------------------
    # 6. Version Java
    # --------------------------------------------------
    titre(rapport, "6. JAVA")

    code, sortie, erreur = commande([
        "docker", "exec", CONTAINER, "java", "-version"
    ])

    rapport.append(sortie or erreur or "Version Java indisponible.")

    # --------------------------------------------------
    # 7. Informations en direct via RCON
    # --------------------------------------------------
    titre(rapport, "7. INFORMATIONS EN DIRECT")

    if etat.get("Running"):
        for cmd in ("version", "list", "plugins"):
            time.sleep(5)
            code, sortie, erreur = commande([
                "docker", "exec", CONTAINER,
                "rcon-cli", cmd
            ], timeout=8)

            rapport.append(f"\nCommande : {cmd}")

            if code == 0:
                rapport.append(sortie or "(aucune réponse)")
            else:
                rapport.append(
                    "Indisponible : "
                    + (erreur or sortie or "commande non accessible")
                )
    else:
        rapport.append(
            "Serveur arrêté : les commandes RCON sont ignorées."
        )

    # --------------------------------------------------
    # 8. Informations Compose
    # --------------------------------------------------
    titre(rapport, "8. PROJET DOCKER COMPOSE")

    labels = config.get("Labels") or {}

    for cle in (
        "com.docker.compose.project",
        "com.docker.compose.service",
        "com.docker.compose.project.config_files",
        "com.docker.compose.project.working_dir"
    ):
        if labels.get(cle):
            rapport.append(f"{cle} : {labels[cle]}")

    if not any(k.startswith("com.docker.compose.") for k in labels):
        rapport.append(
            "Aucune métadonnée Compose trouvée sur le conteneur."
        )

    titre(rapport, "9. LIMITES DU RAPPORT")

    rapport.extend([
        "- Un JAR présent sur disque n'est pas forcément chargé.",
        "- RCON permet de consulter les informations du serveur en direct.",
        "- Les métadonnées d'un plugin ne déclarent pas toujours "
        "les versions Minecraft compatibles.",
        "- La version exacte peut être inconnue si Docker utilise "
        "LATEST ou une version non explicitement déclarée.",
        "- Aucun journal serveur n'a été lu.",
        "- Aucun réglage du serveur n'a été modifié."
    ])

    enregistrer(rapport)


def enregistrer(rapport):
    contenu = "\n".join(rapport) + "\n"

    try:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(contenu, encoding="utf-8")
        print(f"\nRapport créé : {OUTPUT}")
        print(f"Taille : {len(contenu)} caractères")
    except OSError as e:
        print(f"Erreur d'écriture : {e}")
        print(contenu)


if __name__ == "__main__":
    main()
