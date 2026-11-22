"""Hachage des mots de passe.

passlib 1.7.4 n'est plus maintenu et plante avec bcrypt >= 4.1
("password cannot be longer than 72 bytes"). On utilise donc bcrypt
directement ; les hachages existants ($2b$...) restent compatibles.
"""

import bcrypt


def _encode(mot_de_passe: str) -> bytes:
    # bcrypt ne prend en compte que les 72 premiers octets.
    return mot_de_passe.encode("utf-8")[:72]


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return bcrypt.hashpw(_encode(mot_de_passe), bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe_clair: str, mot_de_passe_hache: str) -> bool:
    if not mot_de_passe_hache:
        return False
    try:
        return bcrypt.checkpw(_encode(mot_de_passe_clair), mot_de_passe_hache.encode("utf-8"))
    except ValueError:
        # Hachage invalide en base (ex. mot de passe stocké en clair)
        return False
