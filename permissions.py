"""
Vérifications de permissions.

Toute la logique par-serveur passe maintenant par guild_config (plus par
config.py + un fallback global) : chaque guild a son propre rôle Staff /
Admin Staff, ou aucun tant qu'un admin n'a pas fait /config.

Un membre est toujours considéré staff/admin s'il est propriétaire du
serveur ou a la permission Discord "Administrateur", même sans rôle
configuré — pour ne jamais bloquer un admin qui n'a pas encore fini sa
configuration.
"""
import discord
from discord.ext import commands
from discord import app_commands

import guild_config


def _est_staff(store, membre: discord.Member) -> bool:
    if membre.id == membre.guild.owner_id or membre.guild_permissions.administrator:
        return True
    conf = guild_config.get_config(store, membre.guild.id)
    roles_ids = {r.id for r in membre.roles}
    return conf["staff_role_id"] in roles_ids or conf["admin_role_id"] in roles_ids


def _est_admin_staff(store, membre: discord.Member) -> bool:
    if membre.id == membre.guild.owner_id or membre.guild_permissions.administrator:
        return True
    conf = guild_config.get_config(store, membre.guild.id)
    roles_ids = {r.id for r in membre.roles}
    return conf["admin_role_id"] in roles_ids


def est_staff(store, membre: discord.Member) -> bool:
    """Utilisable hors commandes (ex: callbacks de boutons)."""
    return _est_staff(store, membre)


def est_salon_ticket(store, channel) -> bool:
    """Vérifie qu'un salon fait partie de la catégorie tickets configurée pour sa guild."""
    category_id = guild_config.get(store, channel.guild.id, "ticket_category_id")
    return category_id is not None and getattr(channel, "category_id", None) == category_id


def is_staff_or_higher():
    async def predicate(ctx):
        return _est_staff(ctx.bot.store, ctx.author)
    return commands.check(predicate)


def is_admin_staff_or_higher():
    async def predicate(ctx):
        return _est_admin_staff(ctx.bot.store, ctx.author)
    return commands.check(predicate)


def is_staff_or_higher_app():
    def predicate(interaction: discord.Interaction):
        return _est_staff(interaction.client.store, interaction.user)
    return app_commands.check(predicate)


def is_admin_staff_or_higher_app():
    def predicate(interaction: discord.Interaction):
        return _est_admin_staff(interaction.client.store, interaction.user)
    return app_commands.check(predicate)


def is_server_manager():
    """Réservé aux membres avec la permission 'Gérer le serveur' (ou owner/admin).
    Utilisé pour /config et les commandes de setup — pas besoin d'être
    littéralement le propriétaire pour configurer le bot."""
    def predicate(interaction: discord.Interaction):
        membre = interaction.user
        return (
            membre.id == interaction.guild.owner_id
            or membre.guild_permissions.administrator
            or membre.guild_permissions.manage_guild
        )
    return app_commands.check(predicate)
