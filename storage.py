"""
Couche de persistance.

Même principe que l'ancien bot (Upstash Redis REST, une clé = un dict JSON
sérialisé), regroupé dans une classe unique injectable/testable. La table
supplémentaire "guild_configs" contient la configuration par serveur
(voir guild_config.py) : {str(guild_id): {champ: valeur, ...}}.

⚠️ Note scalabilité, volontairement inchangée par rapport à l'original :
chaque `save(table)` réécrit l'intégralité de la table concernée. Pour un
nombre de serveurs très important avec un fort volume de messages (XP), il
est recommandé à terme de passer à des clés par-serveur
(`levels:{guild_id}`) ou à une vraie base de données (Postgres, SQLite...).
Ce choix n'a pas été fait ici pour rester dans le même style que le bot
d'origine et ne pas complexifier la migration des données existantes.
"""
import json
import aiohttp


class UpstashClient:
    """Petit wrapper autour de l'API REST Upstash Redis."""

    def __init__(self, url: str, token: str):
        if not url or not token:
            raise SystemExit(
                "❌ Il manque UPSTASH_REDIS_REST_URL ou UPSTASH_REDIS_REST_TOKEN "
                "dans les variables d'environnement."
            )
        self._url = url
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _command(self, *args):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._url, headers=self._headers, json=list(args), timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                payload = await resp.json()
        return payload.get("result")

    async def get_json(self, key: str) -> dict:
        try:
            valeur = await self._command("GET", key)
            return json.loads(valeur) if valeur else {}
        except Exception as e:
            print(f"❌ Erreur chargement '{key}' depuis Upstash : {e}")
            return {}

    async def set_json(self, key: str, data: dict) -> None:
        try:
            await self._command("SET", key, json.dumps(data))
        except Exception as e:
            print(f"❌ Erreur sauvegarde '{key}' vers Upstash : {e}")


class DataStore:
    """Regroupe toutes les données persistantes du bot au même endroit."""

    KEYS = (
        "levels", "warns", "mutes", "invites", "giveaways",
        "salon_pauses", "reglement", "role_menus", "avis",
        "tickets_info", "avis_attente", "avis_tickets", "gw_settings",
        "guild_configs",
    )

    def __init__(self, client: UpstashClient):
        self._client = client
        self.levels: dict = {}
        self.warns: dict = {}
        self.mutes: dict = {}
        self.invites: dict = {}
        self.giveaways: dict = {}
        self.gw_settings: dict = {}
        self.salon_pauses: dict = {}
        self.reglement: dict = {}
        self.role_menus: dict = {}
        self.avis: dict = {}
        self.tickets_info: dict = {}
        self.avis_attente: dict = {}
        self.avis_tickets: dict = {}
        # guild_configs : str(guild_id) -> {champ: valeur} (voir guild_config.py)
        self.guild_configs: dict = {}

    async def load_all(self) -> None:
        for key in self.KEYS:
            setattr(self, key, await self._client.get_json(key))
        print("✅ Données chargées depuis Upstash Redis")

    async def save(self, key: str) -> None:
        await self._client.set_json(key, getattr(self, key))
