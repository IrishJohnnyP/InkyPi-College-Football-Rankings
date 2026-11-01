import base64
import logging
import os
import re
from datetime import datetime
from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session

logger = logging.getLogger(__name__)

class CFBRankings(BasePlugin):

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["style_settings"] = True
        return params

    def _find_logo_dir(self):
        """Locate static/logos directory across system service paths."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_dirs = [
            "/home/john/InkyPi/src/static/logos",
            "/home/john/InkyPi/static/logos",
            os.path.abspath(os.path.join(current_dir, "../../static/logos")),
            "/usr/local/inkypi/src/static/logos",
        ]
        for d in candidate_dirs:
            if os.path.isdir(d):
                return d
        return candidate_dirs[0]

    def generate_image(self, settings, device_config):
        url = "https://cfbrankings.butternut.cloud"
        
        season = settings.get("season")
        week = settings.get("week")
        params = {}
        if season: params["season"] = season
        if week: params["week"] = week

        app_key = device_config.load_env_key("app_key")
        if app_key:
            params["app_key"] = app_key

        try:
            session = get_http_session()
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch college football rankings: {e}")
