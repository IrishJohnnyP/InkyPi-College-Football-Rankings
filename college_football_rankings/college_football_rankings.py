from plugins.base_plugin.base_plugin import BasePlugin
from utils.http_client import get_http_session

class CollegeFootballRankings(BasePlugin):
    def generate_image(self, settings, device_config):
        url = "https://college-football-rankings.pietrowicz.workers.dev"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            # Raising a RuntimeError will cleanly display the error in the InkyPi Web UI
            raise RuntimeError(f"Failed to fetch college football rankings: {e}")

        # CFP rankings take precedence if they are available
        poll_data = data.get("cfp", [])
        poll_name = "CFP RANKINGS"
        
        if not poll_data:
            poll_data = data.get("ap", [])
            poll_name = "AP TOP 25"

        # Split the data into two columns: 1-13 and 14-25
        col1 = poll_data[:13]
        col2 = poll_data[13:25]

        # Prepare parameters for Jinja mapping
        template_params = {
            "meta": data.get("meta", {}),
            "poll_name": poll_name,
            "col1": col1,
            "col2": col2,
            "plugin_settings": settings
        }

        # Uses InkyPi's built-in headless Chromium to render the template
        return self.render_image(
            dimensions=(device_config.width, device_config.height),
            html_file="college_football_rankings.html",
            css_file="college_football_rankings.css",
            template_params=template_params
        )
