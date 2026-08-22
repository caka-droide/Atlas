"""
Point d'entrée logique du bot : création du bot, chargement des cogs,
ré-enregistrement des Views persistantes, sync des commandes, erreurs
globales.

Différence majeure avec l'ancien bot : le préfixe texte est calculé
dynamiquement par serveur (get_prefix), puisqu'un même bot tourne
maintenant sur un nombre illimité de serveurs pouvant chacun choisir leur
propre préfixe via /config.
"""
import discord
from discord.ext import commands
from discord import app_commands

import config
import guild_config
from storage import UpstashClient, DataStore
from views.tickets import TicketButton, CloseButton, TicketRequestView, ReglementView, RoleMenuView, AvisTicketView

EXTENSIONS = (
    "cogs.setup_config",
    "cogs.activity",
    "cogs.moderation",
    "cogs.tickets",
    "cogs.invites",
    "cogs.giveaways",
    "cogs.owner",
    "cogs.general",
)


async def get_prefix(bot: "AtlasBot", message: discord.Message):
    prefixe = config.DEFAULT_PREFIX
    if message.guild is not None:
        prefixe = guild_config.get(bot.store, message.guild.id, "prefix") or config.DEFAULT_PREFIX
    return commands.when_mentioned_or(prefixe)(bot, message)


class AtlasBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=get_prefix, intents=intents, help_command=None)
        self.store = DataStore(UpstashClient(config.UPSTASH_URL, config.UPSTASH_TOKEN))
        self._deja_initialise = False

    async def setup_hook(self):
        await self.store.load_all()
        for extension in EXTENSIONS:
            await self.load_extension(extension)

    async def on_ready(self):
        print(f"✅ {config.BOT_NAME} connecté : {self.user} — présent sur {len(self.guilds)} serveur(s)")

        if self._deja_initialise:
            return
        self._deja_initialise = True

        self.add_view(TicketButton())
        self.add_view(CloseButton())
        self.add_view(TicketRequestView())
        self.add_view(AvisTicketView())

        for message_id, data in self.store.reglement.items():
            guild = self.get_guild(data["guild_id"])
            role = guild.get_role(data["role_id"]) if guild else None
            if role:
                self.add_view(ReglementView(role.id), message_id=int(message_id))

        for message_id, data in self.store.role_menus.items():
            guild = self.get_guild(data["guild_id"])
            if guild:
                roles = [r for rid in data.get("role_ids", []) if (r := guild.get_role(rid))]
                if roles:
                    self.add_view(RoleMenuView(roles), message_id=int(message_id))

        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} commandes slash synchronisées (globalement)")
        except discord.HTTPException as e:
            print(f"❌ Erreur sync : {e}")

        await self.get_cog("Invites").refresh_invite_cache()
        self.get_cog("Giveaways").start_loop()

    async def on_guild_join(self, guild: discord.Guild):
        print(f"➕ Rejoint un nouveau serveur : {guild.name} ({guild.id})")

    async def on_message(self, message):
        # Le cog Activity a son propre listener on_message (pause + XP) qui
        # appelle lui-même process_commands au bon moment. On neutralise
        # donc ce on_message par défaut pour ne pas exécuter les commandes
        # deux fois (voir cogs/activity.py).
        pass

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, (commands.MissingPermissions, commands.CheckFailure)):
            await ctx.send("❌ **Accès refusé :** Tu n'as pas les permissions pour cette commande.")
            return
        if isinstance(error, commands.MemberNotFound):
            await ctx.send(f"❌ Membre introuvable : `{error.argument}`. Utilise une mention ou un ID valide.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Il manque un argument (`{error.param.name}`).")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argument invalide. Vérifie la syntaxe de la commande.")
            return
        print(f"❌ Erreur non gérée sur la commande '{ctx.command}' : {error}")

    async def on_error(self, event_method, *args, **kwargs):
        import traceback
        print(f"❌ Erreur non gérée dans l'event '{event_method}' :")
        traceback.print_exc()


bot = AtlasBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.CheckFailure):
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ **Accès refusé :** Commande réservée.", ephemeral=True)
        return
    print(f"❌ Erreur non gérée sur la commande slash '{interaction.command}' : {error}")
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message("❌ Une erreur inattendue est survenue.", ephemeral=True)
        except discord.HTTPException:
            pass
