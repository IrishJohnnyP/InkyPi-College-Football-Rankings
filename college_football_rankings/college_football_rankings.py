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

        try:
            session = get_http_session()
            response = session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch college football rankings: {e}")

        # Map to the 'ranks' array returned by the Cloudflare Worker[span_7](start_span)[span_7](end_span)
        poll_data = data.get("ranks", [])
        
        # Map to the 'poll' string returned by the Worker and uppercase it[span_8](start_span)[span_8](end_span)
        poll_name = data.get("poll", "AP TOP 25").upper()

        # Split the data into two columns: 1-13 and 14-25[span_9](start_span)[span_9](end_span)
        col1 = poll_data[:13]
        col2 = poll_data[13:25]

        # Generate a clean timestamp for the "Last Updated" display[span_10](start_span)[span_10](end_span)
        now = datetime.now().strftime("%b %d, %Y %I:%M %p")

        # Determine if this is the large screen based on the device config width[span_11](start_span)[span_11](end_span)
        dimensions = device_config.get_resolution()
        is_large = dimensions[0] >= 1000
        
        # Reconstruct the 'meta' dictionary that the HTML template expects[span_12](start_span)[span_12](end_span)[span_13](start_span)[span_13](end_span)
        meta_dict = {
            "season": data.get("season", ""),
            "week": data.get("week", "")
        }

        # Prepare parameters for Jinja mapping[span_14](start_span)[span_14](end_span)
        template_params = {
            "meta": meta_dict,
            "poll_name": poll_name,
            "col1": col1,
            "col2": col2,
            "plugin_settings": settings,
            "last_updated": now,
            "is_large": is_large
        }

        # Uses InkyPi's built-in headless Chromium to render the template[span_15](start_span)[span_15](end_span)
        return self.render_image(
            dimensions=dimensions,
            html_file="college_football_rankings.html",
            css_file="college_football_rankings.css",
            template_params=template_params
        )
