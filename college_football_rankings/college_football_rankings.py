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

        poll_data = data.get("ranks", [])
        logo_dir = self._find_logo_dir()
        logger.info(f"[CFBRankings] Active logo directory: {logo_dir}")

        for team in poll_data:
            school = team.get("school", "")
            
            # Sanitize the exact same way as download_logos.py
            safe_name = school.lower().replace('&', 'and')
            safe_name = re.sub(r'[^a-z0-9]', '_', safe_name)
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')

            candidate_files = [f"{safe_name}.png", f"{safe_name}.jpg", f"{safe_name}.svg"]
            logo_b64 = None

            for c_file in candidate_files:
                full_path = os.path.join(logo_dir, c_file)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "rb") as img_f:
                            encoded = base64.b64encode(img_f.read()).decode("utf-8")
                            ext = "svg+xml" if c_file.endswith(".svg") else "png"
                            logo_b64 = f"data:image/{ext};base64,{encoded}"
                            break
                    except Exception as img_err:
                        logger.warning(f"[CFBRankings] Error reading logo {full_path}: {img_err}")

            if not logo_b64:
                logger.warning(f"[CFBRankings] Logo file missing for '{school}' (expected '{safe_name}.png' in {logo_dir})")

            team["local_logo"] = logo_b64

        poll_name = data.get("poll", "AP TOP 25").upper()

        midpoint = (len(poll_data) + 1) // 2
        col1 = poll_data[:midpoint]
        col2 = poll_data[midpoint:]

        now = datetime.now().strftime("%b %d, %Y %I:%M %p")
        dimensions = device_config.get_resolution()
        is_large = dimensions[0] >= 1000
        
        meta_dict = {
            "season": data.get("season", ""),
            "week": data.get("week", "")
        }

        template_params = {
            "meta": meta_dict,
            "poll_name": poll_name,
            "col1": col1,
            "col2": col2,
            "plugin_settings": settings,
            "last_updated": now,
            "is_large": is_large
        }

        return self.render_image(
            dimensions=dimensions,
            html_file="college_football_rankings.html",
            css_file="college_football_rankings.css",
            template_params=template_params
        )
