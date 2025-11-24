"""Data handler for the response from the Yandex API"""
from datetime import datetime, timedelta
import json
from dateutil import parser
import xmltodict
import re


def check_key(element, *keys):
    """
    Check if *keys (nested) exists in `element` (dict).
    """
    if not isinstance(element, dict):
        raise AttributeError("keys_exists() expects dict as first argument.")
    if len(keys) == 0:
        raise AttributeError("keys_exists() expects at least two arguments, one given.")

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

def diff_minutes(iso_date1: str, iso_date2: str) -> int:
    """
    Возвращает разницу между двумя датами ISO 8601 в минутах.
    """
    dt1 = parser.isoparse(iso_date1)
    dt2 = parser.isoparse(iso_date2)

    diff = dt2 - dt1
    return int(diff.total_seconds() // 60)


class ApiData:
    """Data handler class for the response from the Yandex API"""

    def __init__(self, time_offset):
        self.raw_result = ""
        self._last_update = None
        self._api_json = []
        self._station_name = ""
        self.time_offset = time_offset
        self._refresh_interval = 2

    def populate(self, json_data):
        """Hydrate the data entity with the XML API response"""
        self.raw_result = json_data
        self._api_json = []
        self._last_update = datetime.now()
    
    def get_data(self):
        """Parse JSON raw data and return nearest future segment (stored in _api_xml)"""
        if not self.raw_result:
            return None

        # Если уже был вычислен — вернуть кэш
        if self._api_json:
            return self._api_json

        # Парсим JSON
        try:
            data = self.raw_result
        except Exception as e:
            return None

        segments = data.get("segments", [])
        if not segments:
            return None


        now = datetime.now().astimezone()
        target_time = now + timedelta(minutes=self.time_offset)
        target_iso = target_time.isoformat(timespec="seconds")

        # future segments
        future = [s for s in segments if s.get("departure", "") > target_iso]

        if not future:
            return None

        # nearest
        future.sort(key=lambda s: s["departure"])
        nearest = future[0]

        self._api_json = nearest

        return self._api_json

    def is_empty(self):
        """Check if the entity is empty"""
        return len(self._api_json) == 0

    def get_destination_data(self, station):
        """Get the destination data"""
        data = self.get_data()
        if data and check_key(data, "departures"):
            destinations = data["departures"]["destination"]
            if destinations:
                if isinstance(destinations, dict):
                    if destinations["@crs"] == station:
                        service = destinations["service"]
                        if check_key(service, "serviceType"):
                            return service
                else:
                    for destination in destinations:
                        if destination["@crs"] == station:
                            service = destination["service"]
                            if check_key(service, "serviceType"):
                                return service

    def get_service_details(self, crx):
        """Get the destinations service details data"""
        data = self.get_destination_data(crx)
        if data:
            cloned_data = data.copy()
            del cloned_data["subsequentCallingPoints"]
            return cloned_data

    def get_calling_points(self, crx):
        """Get the stations the service stops at on route to the destination"""
        data = self.get_destination_data(crx)
        if data:
            callingPoints = data["subsequentCallingPoints"]["callingPointList"]["callingPoint"]
            return callingPoints if type(callingPoints) in [list, tuple] else [callingPoints] 

    def get_station_name(self):
        """Get the name of the station to watch for departures"""
        if not self._station_name:
            data = self.get_data()
            if data:
                name = data["from"]["title"]
                if name:
                    self._station_name = name

        return self._station_name

    def get_destination_name(self):
        """Get the name of the final destination station"""
        data = self.get_data()
        if data:
            if check_key(data, "to"):
                return data["to"]["title"]

    def get_last_update(self):
        """Get the time the data was populated"""
        return self._last_update

    def get_state(self, crx):
        """Get the state of the data based on destination"""
        data = self.get_data()
        if data:
            return datetime.fromisoformat(data["departure"]).strftime("%H:%M")
        return "None"
    def get_thread(self):
            
        data = self.get_data()
        if data:
            return "None"
        return "None"