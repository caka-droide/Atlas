"""Cog: commandes utilisées à l'intérieur d'un salon de ticket."""
import discord
from discord.ext import commands

import config
import guild_config
import utils
from permissions import is_staff_or_higher, est_salon_ticket
from views.tickets import ConfirmCloseView


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = bot.store

    @commands.hybrid_command(name="rename")
    @is_staff_or_higher()
    async def rename_cmd(self, ctx, *, nouveau_nom: str):
        if not est_salon_ticket(self.store, ctx.channel):
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon de ticket.")
            return

        nouveau_nom_propre = nouveau_nom.lower().strip().replace(" ", "-")[:100]
        ancien_nom = ctx.channel.name

        try:
            await ctx.channel.edit(name=nouveau_nom_propre)
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de renommer ce salon.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"❌ Impossible de renommer ce salon : {e}")
            return

        await ctx.send(f"✅ Ticket renommé en `{nouveau_nom_propre}`.")
        await utils.envoyer_log(
            self.store, ctx.guild, "✏️ Ticket renommé", f"`{ancien_nom}` → `{nouveau_nom_propre}` par {ctx.author.mention}",
            config.Couleurs.DEFAUT, ctx.author,
        )

    @commands.hybrid_command(name="close")
    @is_staff_or_higher()
    async def close_cmd(self, ctx):
        if not est_salon_ticket(self.store, ctx.channel):
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon de ticket.")
            return

        staff_role_id = guild_config.get(self.store, ctx.guild.id, "staff_role_id")
        admin_role_id = guild_config.get(self.store, ctx.guild.id, "admin_role_id")
        pings = [f"<@&{rid}>" for rid in (staff_role_id, admin_role_id) if rid]

        embed = discord.Embed(
            description=f"⚠️ **{ctx.author.mention} souhaite fermer ce ticket.** Confirme ci-dessous.",
            color=config.Couleurs.ERREUR,
        )
        await ctx.send(" ".join(pings) if pings else None, embed=embed, view=ConfirmCloseView())

    @commands.hybrid_command(name="staff")
    @is_staff_or_higher()
    async def staff_cmd(self, ctx, membre: discord.Member):
        if not est_salon_ticket(self.store, ctx.channel):
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon de ticket.")
            return
        try:
            await ctx.channel.set_permissions(membre, read_messages=True, send_messages=True,
                                               reason=f"Ajouté au ticket par {ctx.author}")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de modifier les accès de ce salon.")
            return

        await ctx.send(f"✅ {membre.mention} a été ajouté à ce ticket.")
        await utils.envoyer_log(
            self.store, ctx.guild, "➕ Staff ajouté au ticket",
            f"{membre.mention} ajouté au ticket {ctx.channel.mention} par {ctx.author.mention}",
            config.Couleurs.SUCCES, ctx.author,
        )

    @commands.hybrid_command(name="unstaff")
    @is_staff_or_higher()
    async def unstaff_cmd(self, ctx, membre: discord.Member):
        if not est_salon_ticket(self.store, ctx.channel):
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon de ticket.")
            return
        try:
            await ctx.channel.set_permissions(membre, overwrite=None, reason=f"Retiré du ticket par {ctx.author}")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de modifier les accès de ce salon.")
            return

        await ctx.send(f"✅ {membre.mention} a été retiré de ce ticket.")
        await utils.envoyer_log(
            self.store, ctx.guild, "➖ Staff retiré du ticket",
            f"{membre.mention} retiré du ticket {ctx.channel.mention} par {ctx.author.mention}",
            config.Couleurs.ORANGE_KICK, ctx.author,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
