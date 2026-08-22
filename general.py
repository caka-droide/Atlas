"""Cog: commandes générales accessibles à tous (aide, stats, avis)."""
import discord
from discord import app_commands
from discord.ext import commands

import config
import guild_config
import utils


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = bot.store

    @commands.hybrid_command()
    async def help(self, ctx):
        prefixe = guild_config.get(self.store, ctx.guild.id, "prefix") or config.DEFAULT_PREFIX if ctx.guild else config.DEFAULT_PREFIX
        embed = discord.Embed(
            title=f"📚 Menu d'aide — {config.BOT_NAME}",
            description="Voici la liste des commandes disponibles, classées par permissions.",
            color=config.Couleurs.INFO_SOMBRE,
        )
        embed.add_field(name="👥 Membres", value=(
            f"`{prefixe}i` / `/invitations` : Voir tes invitations.\n"
            "`/niveau` : Consulter ton niveau d'XP.\n"
            "`/classement` : Voir le classement XP du serveur.\n"
            "`/avis` : Laisser un avis sur le serveur.\n"
            "`/avis_stats` : Voir les stats des avis.\n"
            "`/avis_staff` : Voir la moyenne des avis tickets d'un staff.\n"
            "`/stats` : Voir les statistiques du serveur."
        ), inline=False)
        embed.add_field(name="🛡️ Staff", value=(
            f"`{prefixe}warn @membre raison` : Avertir un membre.\n"
            f"`{prefixe}warns [@membre]` : Voir les avertissements.\n"
            f"`{prefixe}unwarn @membre` : Retirer les avertissements.\n"
            f"`{prefixe}mute @membre durée raison` : Timeout natif (ex : `3m`, `1h`, `1d`).\n"
            f"`{prefixe}unmute @membre` : Retirer le mute.\n"
            f"`{prefixe}lock` / `{prefixe}unlock` : Verrouiller/déverrouiller le salon.\n"
            f"`{prefixe}rename nom` : Renommer le ticket en cours.\n"
            f"`{prefixe}close` : Demander la fermeture du ticket en cours.\n"
            f"`{prefixe}staff @membre` / `{prefixe}unstaff @membre` : Gérer l'accès à un ticket.\n"
            "`/clear` : Supprimer des messages."
        ), inline=False)
        embed.add_field(name="🔨 Admin Staff", value=(
            f"`{prefixe}kick @membre raison` : Expulser du serveur.\n"
            f"`{prefixe}ban @membre raison` : Bannir du serveur.\n"
            "`/unban` : Débannir un membre.\n"
            "`/slowmode` : Régler le mode lent d'un salon.\n"
            "`/pause` : Mettre un salon en cooldown global.\n"
            "`/gw` / `/gw_reroll` / `/gw_end` : Gérer les giveaways."
        ), inline=False)
        embed.add_field(name="👑 Gestionnaires du serveur", value=(
            "`/config` : Panel de configuration complet du bot.\n"
            "`/setup_ticket` / `/setup_reglement` / `/setup_roles` : Poster les panels correspondants."
        ), inline=False)
        embed.set_footer(text=f"Demandé par {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @app_commands.command(name="log", description="Redirige vers le salon des logs")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def log_cmd(self, interaction: discord.Interaction):
        salon_id = guild_config.get(self.store, interaction.guild.id, "logs_channel_id")
        salon_logs = interaction.guild.get_channel(salon_id) if salon_id else None
        embed = discord.Embed(
            title="📋 Suivi des logs",
            description=f"Toutes les actions sont enregistrées dans {salon_logs.mention if salon_logs else 'un salon non configuré (`/config`)'}.",
            color=config.Couleurs.DEFAUT,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="Statistiques du serveur")
    async def stats_cmd(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"📊 Stats de {guild.name}", color=config.Couleurs.DEFAUT)
        embed.add_field(name="👥 Membres", value=str(guild.member_count))
        utils.config_embed_footer(embed)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avis", description="Laisser un avis")
    @app_commands.choices(note=[app_commands.Choice(name=f"{i} étoiles", value=i) for i in range(1, 6)])
    async def avis_cmd(self, interaction: discord.Interaction, theme: str,
                        note: app_commands.Choice[int], texte: str, image: discord.Attachment = None):
        etoiles = "⭐" * note.value + "☆" * (5 - note.value)
        embed = discord.Embed(title="📝 Nouvel avis", color=config.Couleurs.JAUNE)
        embed.add_field(name="Thème", value=theme, inline=True)
        embed.add_field(name="Note", value=f"{etoiles} ({note.value}/5)", inline=True)
        embed.add_field(name="Avis", value=texte, inline=False)
        if image:
            embed.set_image(url=image.url)
        await interaction.response.send_message(embed=embed)

        gid = str(interaction.guild.id)
        self.store.avis.setdefault(gid, []).append({
            "theme": theme, "note": note.value, "texte": texte,
            "image_url": image.url if image else None, "auteur_id": interaction.user.id,
        })
        await self.store.save("avis")

    @app_commands.command(name="avis_stats", description="Voir la moyenne des avis")
    async def avis_stats_cmd(self, interaction: discord.Interaction, theme: str = None):
        gid = str(interaction.guild.id)
        tous_avis = self.store.avis.get(gid, [])
        avis_liste = [a for a in tous_avis if a["theme"].lower() == theme.lower()] if theme else tous_avis
        if not avis_liste:
            await interaction.response.send_message("❌ Aucun avis trouvé.", ephemeral=True)
            return

        moyenne = sum(a["note"] for a in avis_liste) / len(avis_liste)
        arrondi = round(moyenne)
        embed = discord.Embed(title="📊 Avis", color=config.Couleurs.JAUNE)
        embed.add_field(name="Moyenne", value=f"{'⭐' * arrondi}{'☆' * (5 - arrondi)} ({moyenne:.1f}/5)")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avis_staff", description="Voir la moyenne des avis tickets d'un membre du staff")
    async def avis_staff_cmd(self, interaction: discord.Interaction, staff: discord.Member):
        gid = str(interaction.guild.id)
        avis_du_staff = [a for a in self.store.avis_tickets.get(gid, []) if a["staff_id"] == staff.id]
        if not avis_du_staff:
            await interaction.response.send_message(f"❌ Aucun avis de ticket trouvé pour {staff.mention}.", ephemeral=True)
            return

        moyenne = sum(a["note"] for a in avis_du_staff) / len(avis_du_staff)
        arrondi = round(moyenne)
        embed = discord.Embed(title=f"📊 Avis tickets — {staff.display_name}", color=config.Couleurs.JAUNE)
        embed.add_field(name="Moyenne", value=f"{'⭐' * arrondi}{'☆' * (5 - arrondi)} ({moyenne:.2f}/5)", inline=False)
        embed.add_field(name="Nombre d'avis", value=str(len(avis_du_staff)), inline=False)
        embed.set_thumbnail(url=staff.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
