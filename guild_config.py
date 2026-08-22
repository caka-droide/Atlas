"""
Configuration par-serveur, 100% dynamique.

C'est le cœur de la différence avec l'ancien bot : au lieu d'IDs codés en
dur dans config.py (+ un fichier guild_settings.json en lecture seule pour
un deuxième serveur), CHAQUE serveur a sa propre configuration, modifiable
en direct par un admin via /config, et persistée dans le DataStore (table
"guild_configs", une entrée par guild).

Un serveur qui n'a rien configuré a simplement des valeurs à None : les
fonctionnalités concernées se désactivent proprement (message clair
invitant à faire /config) plutôt que de pointer par erreur vers un salon
ou un rôle d'un AUTRE serveur, comme ça aurait été le cas avec un simple
fallback global.
"""
from __future__ import annotations

# Liste unique de vérité pour tous les champs configurables. Le panel
# /config (views/config_panel.py) et l'embed récapitulatif en dérivent
# leur contenu, donc ajouter un champ ici + dans le panel suffit à
# l'exposer partout.
FIELDS = (
    "welcome_channel_id",
    "leave_channel_id",
    "logs_channel_id",
    "ticket_logs_channel_id",
    "ticket_category_id",
    "ticket_request_channel_id",
    "reviews_channel_id",
    "staff_role_id",
    "admin_role_id",
    "prefix",
)

LABELS = {
    "welcome_channel_id": "Salon de bienvenue",
    "leave_channel_id": "Salon des départs",
    "logs_channel_id": "Salon des logs",
    "ticket_logs_channel_id": "Salon des logs de tickets (transcripts)",
    "ticket_category_id": "Catégorie des tickets",
    "ticket_request_channel_id": "Salon des demandes de tickets",
    "reviews_channel_id": "Salon des avis de tickets",
    "staff_role_id": "Rôle Staff",
    "admin_role_id": "Rôle Admin Staff",
    "prefix": "Préfixe texte",
}

DEFAULTS = {field: None for field in FIELDS}
DEFAULTS["prefix"] = None  # None => on utilisera config.DEFAULT_PREFIX


def get_config(store, guild_id: int) -> dict:
    """Renvoie la configuration complète (avec défauts) d'une guild."""
    conf = store.guild_configs.get(str(guild_id), {})
    return {**DEFAULTS, **conf}


def get(store, guild_id: int, key: str):
    return get_config(store, guild_id).get(key)


async def set_value(store, guild_id: int, key: str, value) -> None:
    gid = str(guild_id)
    store.guild_configs.setdefault(gid, {})
    if value is None:
        store.guild_configs[gid].pop(key, None)
    else:
        store.guild_configs[gid][key] = value
    await store.save("guild_configs")


async def reset_all(store, guild_id: int) -> None:
    store.guild_configs.pop(str(guild_id), None)
    await store.save("guild_configs")


def is_tickets_ready(store, guild_id: int) -> bool:
    conf = get_config(store, guild_id)
    return bool(
        conf["ticket_category_id"]
        and conf["ticket_request_channel_id"]
        and (conf["staff_role_id"] or conf["admin_role_id"])
    )


def missing_fields(store, guild_id: int) -> list[str]:
    conf = get_config(store, guild_id)
    return [f for f in FIELDS if f != "prefix" and not conf[f]]


def completion_ratio(store, guild_id: int) -> tuple[int, int]:
    total = len(FIELDS) - 1  # on ne compte pas le préfixe (optionnel par nature)
    manquants = len(missing_fields(store, guild_id))
    return total - manquants, total
