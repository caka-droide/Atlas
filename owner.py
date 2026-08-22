"""Cog: commandes réservées au propriétaire du bot + panels de setup serveur."""
import discord
from discord import app_commands
from discord.ext import commands

import config
import utils
from permissions import is_server_manager
from views.tickets import ReglementView, RoleMenuView, TicketButton


class Owner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = bot.store

    # ── Gestion des serveurs où se trouve le bot (propriétaire du BOT, pas du serveur) ──
    @commands.command()
    @commands.is_owner()
    async def guilds(self, ctx):
        """!guilds -> liste tous les serveurs où le bot est présent, avec leur ID."""
        serveurs = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)
        if not serveurs:
            await ctx.send("Le bot n'est dans aucun serveur.")
            return

        chunks = [serveurs[i:i + 20] for i in range(0, len(serveurs), 20)]
        for i, chunk in enumerate(chunks, start=1):
            embed = discord.Embed(
                title=f"🌐 Serveurs du bot ({len(serveurs)})" + (f" — page {i}/{len(chunks)}" if len(chunks) > 1 else ""),
                color=config.Couleurs.INFO_SOMBRE,
            )
            for g in chunk:
                embed.add_field(name=g.name, value=f"ID : `{g.id}`\nMembres : {g.member_count}", inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            await ctx.send("❌ Le bot n'est dans aucun serveur avec cet ID.")
            return
        nom = guild.name
        await guild.leave()
        await ctx.send(f"✅ Le bot a quitté le serveur **{nom}** (`{guild_id}`).")

    # ── Identité du bot ───────────────────────────────────────────────────
    @commands.command()
    @commands.is_owner()
    async def setbotname(self, ctx, *, nouveau_nom: str):
        try:
            await self.bot.user.edit(username=nouveau_nom)
            await ctx.send(f"✅ Nom du bot changé en : **{nouveau_nom}**")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Erreur lors du changement de nom : {e}")

    @commands.command()
    @commands.is_owner()
    async def setpdp(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("❌ Tu dois attacher une image à ton message pour changer la photo de profil.")
            return
        try:
            image_bytes = await ctx.message.attachments[0].read()
            await self.bot.user.edit(avatar=image_bytes)
            await ctx.send("✅ Photo de profil mise à jour !")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Erreur lors du changement d'avatar : {e}")

    # ── Setup serveur (accessible à tout gestionnaire du serveur, pas au seul owner du bot) ──
    @app_commands.command(name="setup_ticket", description="Poster le panel pour créer des tickets")
    @is_server_manager()
    async def setup_ticket_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📞 Support et tickets",
            description=(
                "Clique sur le bouton ci-dessous pour ouvrir un ticket. "
                "On te demandera la raison de ta demande, puis le staff devra la valider."
            ),
            color=config.Couleurs.INFO_SOMBRE,
        )
        utils.config_embed_footer(embed)
        await interaction.channel.send(embed=embed, view=TicketButton())
        await interaction.response.send_message(
            "✅ Panel créé. Pense à configurer les salons/rôles de tickets avec `/config` si ce n'est pas déjà fait.",
            ephemeral=True,
        )

    @app_commands.command(name="setup_reglement", description="Poster le règlement")
    @is_server_manager()
    async def setup_reglement_cmd(self, interaction: discord.Interaction, role: discord.Role,
                                   texte: str, salon: discord.TextChannel = None):
        cible = salon or interaction.channel
        embed = discord.Embed(
            title="📜 Règlement du serveur", description=texte.replace("\\n", "\n"),
            color=config.Couleurs.INFO_SOMBRE,
        )
        utils.config_embed_footer(embed)
        view = ReglementView(role.id)
        message = await cible.send(embed=embed, view=view)
        self.store.reglement[str(message.id)] = {
            "guild_id": interaction.guild.id, "channel_id": cible.id, "role_id": role.id,
        }
        await self.store.save("reglement")
        self.bot.add_view(view, message_id=message.id)
        await interaction.response.send_message("✅ Règlement posté.", ephemeral=True)

    @app_commands.command(name="setup_roles", description="Poster un menu de rôles")
    @is_server_manager()
    async def setup_roles_cmd(self, interaction: discord.Interaction, role1: discord.Role,
                               role2: discord.Role = None, salon: discord.TextChannel = None):
        cible = salon or interaction.channel
        roles = [r for r in [role1, role2] if r is not None]
        embed = discord.Embed(title="🎭 Choisis tes rôles", description="Sélectionne tes rôles.",
                               color=config.Couleurs.DEFAUT)
        utils.config_embed_footer(embed)
        view = RoleMenuView(roles)
        message = await cible.send(embed=embed, view=view)
        self.store.role_menus[str(message.id)] = {
            "guild_id": interaction.guild.id, "channel_id": cible.id, "role_ids": [r.id for r in roles],
        }
        await self.store.save("role_menus")
        self.bot.add_view(view, message_id=message.id)
        await interaction.response.send_message("✅ Menu créé.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
