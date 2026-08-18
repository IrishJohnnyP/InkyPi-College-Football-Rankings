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
        
        # Pass season and week settings to Cloudflare Worker if configured
        season = settings.get("season")
        week = settings.get("week")
        params = {}
        if season: params["season"] = season
        if week: params["week"] = week

        # --- SECURITY FIX ---
        # Retrieve the app_key from InkyPi's environment and include it in query params
        app_key = device_config.load_env_key("app_key")
        if app_key:
            params["app_key"] = app_key
        # --------------------

        try:
            session = get_http_session()
            response = session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch college football rankings: {e}")

        # Map to the 'ranks' array returned by the Cloudflare Worker
        poll_data = data.get("ranks", [])
        
        # Map to the 'poll' string returned by the Worker and uppercase it
        poll_name = data.get("poll", "AP TOP 25").upper()

        # Split the data into two columns: 1-13 and 14-25
        col1 = poll_data[:13]
        col2 = poll_data[13:25]

        # Generate a clean timestamp for the "Last Updated" display
        now = datetime.now().strftime("%b %d, %Y %I:%M %p")

        # Determine if this is the large screen based on the device config width
        dimensions = device_config.get_resolution()
        is_large = dimensions[0] >= 1000
        
        # Reconstruct the 'meta' dictionary that the HTML template expects
        meta_dict = {
            "season": data.get("season", ""),
            "week": data.get("week", "")
        }

        # Prepare parameters for Jinja mapping
        template_params = {
            "meta": meta_dict,
            "poll_name": poll_name,
            "col1": col1,
            "col2": col2,
            "plugin_settings": settings,
            "last_updated": now,
            "is_large": is_large
        }

        # Uses InkyPi's built-in headless Chromium to render the template
        return self.render_image(
            dimensions=dimensions,
            html_file="college_football_rankings.html",
            css_file="college_football_rankings.css",
            template_params=template_params
        )
