from dataclasses import dataclass
from datetime import datetime


@dataclass
class TransferRumor:
    player_name: str
    from_team: str
    to_team: str | None
    rumored_fee: str | None
    source_url: str
    confidence: str  # high, medium, low
    published: datetime | None


class TransfermarktClient:
    """
    Placeholder for Transfermarkt scraping.
    Actual scraping requires browser emulation (JS rendering) and careful rate limiting.
    Use third-party APIs (e.g., Sportmonks, API-FOOTBALL) in production.
    """

    async def get_transfer_rumors(self, team_name: str, limit: int = 10) -> list[TransferRumor]:
        return []

    async def get_team_transfers(self, team_name: str, window: str = "latest") -> list[dict]:
        return []


transfermarkt = TransfermarktClient()
