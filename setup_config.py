"""Cog: la commande /config (panel de configuration par serveur)."""
import discord
from discord import app_commands
from discord.ext import commands

from permissions import is_server_manager
from views.config_panel import ConfigMainView, build_overview_embed


class SetupConfig(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.store = bot.store

    @app_commands.command(name="config", description="Ouvrir le panel de configuration du bot pour ce serveur")
    @is_server_manager()
    async def config_cmd(self, interaction: discord.Interaction):
        embed = build_overview_embed(interaction.guild, self.store)
        view = ConfigMainView(self.store, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @config_cmd.error
    async def config_cmd_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ Cette commande est réservée aux membres ayant la permission **Gérer le serveur**.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupConfig(bot))
