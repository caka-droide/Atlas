"""
Configuration globale du bot.

Contrairement à l'ancien bot (mono-serveur, IDs de salons/rôles codés en
dur), CE bot est prévu pour tourner sur un nombre illimité de serveurs.
Il n'y a donc plus AUCUN identifiant Discord (salon, rôle, catégorie) codé
en dur ici : chaque serveur configure les siens en direct via la commande
/config (voir guild_config.py + cogs/setup_config.py).

Ce fichier ne contient que ce qui est réellement global : le nom du bot,
les secrets d'environnement, et le thème visuel (couleurs/emojis) partagé
par tous les serveurs.
"""
import os

# ── Identité du bot ───────────────────────────────────────────────────────
# Change simplement cette valeur : elle est utilisée dans les embeds, le
# footer, etc. Le "vrai" nom/avatar du bot (ceux visibles dans Discord) se
# changent eux depuis le Developer Portal (ou avec la commande owner
# +setbotname / +setpdp).
BOT_NAME = "Atlas"
BOT_TAGLINE = "Gestion de serveur nouvelle génération"

# ── Secrets / environnement ────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN")
UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

# ── Préfixe texte (secondaire, les commandes principales sont en slash) ────
DEFAULT_PREFIX = "!"

# ── XP / Niveaux ────────────────────────────────────────────────────────────
XP_PAR_MESSAGE = 15
XP_COOLDOWN_SECONDS = 60

ROLES_NIVEAUX = {
    5: "Niveau 5",
    10: "Niveau 10",
    20: "Niveau 20",
    50: "Niveau 50",
}

# ── Giveaways ───────────────────────────────────────────────────────────────
GIVEAWAY_EMOJI = "🎉"
GIVEAWAY_CHECK_INTERVAL_SECONDS = 30
DEFAULT_GIVEAWAY_BONUS_PERCENT = 0.5

# ── Thème visuel ──────────────────────────────────────────────────────────
class Couleurs:
    DEFAUT = 0x5865F2       # Blurple
    SUCCES = 0x57F287
    ERREUR = 0xED4245
    AVERTISSEMENT = 0xFEE75C
    DANGER_VIF = 0xE74C3C
    NEUTRE = 0x99AAB5
    INFO_SOMBRE = 0x2B2D31
    OR = 0xFAA61A
    JAUNE = 0xF1C40F
    ORANGE_KICK = 0xE67E22

