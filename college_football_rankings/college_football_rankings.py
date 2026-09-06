import base64
import os
import re
from datetime import datetime
from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session

class CFBRankings(BasePlugin):

    def generate_settings_template(self):
        params = super().generate_settings_template()
        params["style_settings"] = True
        return params
         
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
        
        # Locate static/logos relative to this plugin script's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_dir = os.path.abspath(os.path.join(current_dir, "../../static/logos"))
        if not os.path.exists(logo_dir):
            logo_dir = os.path.expanduser("~/InkyPi/src/static/logos")

        # Encode local PNG files directly into inline Base64 data URIs
        for team in poll_data:
            school = team.get("school", "")
            safe_name = school.lower().replace('&', 'and')
            safe_name = re.sub(r'[^a-z0-9]', '_', safe_name)
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')
            
            logo_path = os.path.join(logo_dir, f"{safe_name}.png")
            
            if os.path.exists(logo_path):
                try:
                    with open(logo_path, "rb") as img_file:
                        b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                        team["local_logo"] = f"data:image/png;base64,{b64_data}"
                except Exception:
                    team["local_logo"] = None
            else:
                team["local_logo"] = None

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
