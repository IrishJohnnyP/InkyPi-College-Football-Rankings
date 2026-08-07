from datetime import datetime
from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session

WORKER_URL = "https://cfbrankings.butternut.cloud"


class CFBRankings(BasePlugin):

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["style_settings"] = True
        return params

    def _fetch_rankings(self, season, week):
        session = get_http_session()

        params = {}
        if season:
            params["season"] = season
        if week:
            params["week"] = week

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = session.get(WORKER_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def generate_image(self, settings, device_config):
        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        season = settings.get("season")
        if not season:
            try:
                season = str(datetime.now().year)
            except Exception:
                season = "2026"

        week = settings.get("week") or "1"

        data = self._fetch_rankings(season, week)

        return self.render_image(
            dimensions,
            "college_football_rankings.html",
            "college_football_rankings.css",
            {
                "ranks": data.get("ranks", []),
                "season": data.get("season", season),
                "week": data.get("week", week),
                "poll": data.get("poll", "AP Top 25"),
                "plugin_settings": settings
            }
        )
