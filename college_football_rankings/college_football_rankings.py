import base64
import logging
import os
import re
import traceback
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
        try:
            url = "https://cfbrankings.butternut.cloud"
            
            season = settings.get("season")
            week = settings.get("week")
            params = {}
            if season: params["season"] = season
            if week: params["week"] = week

            app_key = device_config.load_env_key("app_key")
            if app_key:
                params["app_key"] = app_key

            session = get_http_session()
            response = session.get(url, params=params, timeout=(3.05, 15))
            response.raise_for_status()
            data = response.json()
            
            # Defensive check in case the API returns an unexpected array or string
            if not isinstance(data, dict):
                data = {}

            poll_data = data.get("ranks")
            if not isinstance(poll_data, list):
                poll_data = []

            logo_dir = self._find_logo_dir()
            logger.info(f"[CFBRankings] Active logo directory: {logo_dir}")

            for team in poll_data:
                school = team.get("school", "")
                
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

                team["local_logo"] = logo_b64

            # CRITICAL FIX: Safely parse the poll name without risking NoneType crashes
            raw_poll = data.get("poll")
            if not raw_poll:
                raw_poll = "AP TOP 25"
                
            raw_poll_name = str(raw_poll).upper()
            
            # Rename the lengthy API string to a cleaner display name for the InkyPi
            if "PLAYOFF" in raw_poll_name:
                poll_name = "CFP RANKINGS"
            else:
                poll_name = raw_poll_name

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
            
        except Exception as e:
            # Forces InkyPi to print a detailed traceback if anything fails inside this plugin
            logger.error(f"[CFBRankings] Fatal crash in generate_image:\n{traceback.format_exc()}")
            return None
