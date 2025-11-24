"""API wrapper for generating the XML envelope and fetching data from the Yandex API"""
from datetime import datetime
import aiohttp
import async_timeout

from .apidata import ApiData


class Api:
    """API wrapper for generating the XML envelope and fetching data from the Yandex API"""

    def __init__(self, api_key, station, destination, request_url):
        self.api_key = api_key
        self.request_url = request_url
        self.time_offset = 0
        self.time_window = 120
        self.station = station
        self.destination = destination
        self.filters = [destination]
        self.data = ApiData(self.time_offset)

    def set_config(self, key, val):
        """Set config item, such as time_offset and time_window"""
        if key == "time_offset":
            self.time_offset = val
            return True

        if key == "time_window":
            self.time_window = val
            return True

    def generate_filter_list(self):
        """Generate XML Destination Filters"""
        stations = self.filters
        payload = ""

        for station in stations:
            if station is not None:
                payload += f"<ldb:crs>{station}</ldb:crs>\n"

        return payload

    def generate_params(self):
        station = self.station
        destanation = self.destination
        today = datetime.now().strftime("%Y-%m-%d")

        params = {'format': 'json', 'from': station, 'to': destanation, "lang": "ru_RU", "transport_types": "suburban", "limit": 200, "date": today}

        return params

    async def api_request(self):
        """
        To minimise multiple API calls, check if a request from another entity in this component is already in progress.
        If no request is running, generate SOAP Envelope and submit request to Yandex API.
        Otherwise, wait until the existing one is complete, and return that value.
        """
        params = self.generate_params()
        return await self.request(self.request_url, params)

    async def fetch(self, session, url, params):
        """Fetch JSON data from the Darwin API"""
        try:
            async with async_timeout.timeout(15):
                async with session.get(
                    url,
                    headers={
                        "Authorization": self.api_key
                    },
                    params=params,
                ) as response:

                    if response.status != 200:
                        return None

                    # Получаем JSON
                    result = await response.json()

                    if result:
                        self.data.populate(result)

                    return result

        except Exception:
            return None

    async def request(self, url, params):
        """Prepare core request"""
        async with aiohttp.ClientSession() as session:
            return await self.fetch(session, url, params)
