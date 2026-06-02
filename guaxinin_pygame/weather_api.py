"""
Weather API integration for fetching real-time weather and moon data
"""
import requests
import json
from datetime import datetime
import math


class WeatherAPI:
    def __init__(self):
        self.lat = None
        self.lon = None
        self.hemisphere = "south"
        self.timezone = None
        self.weather_data = {
            "temp": None,
            "feels_like": None,
            "humidity": None,
            "windspeed": None,
            "condition": None,
            "weather_code": None,
            "sunrise": None,
            "sunset": None,
        }
        self.moon_phase = 0.0  # 0 = new moon, 0.5 = full moon
        self.moon_illumination = 0.0
        
    def get_location_coords(self, city_name):
        """Get latitude and longitude for a city using Nominatim"""
        try:
            url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={city_name}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data and len(data) > 0:
                self.lat = float(data[0]["lat"])
                self.lon = float(data[0]["lon"])
                self.hemisphere = "south" if self.lat < 0 else "north"
                return True
            return False
        except Exception as e:
            print(f"Error fetching location: {e}")
            return False
    
    def fetch_weather(self):
        """Fetch weather data from Open-Meteo API"""
        if self.lat is None or self.lon is None:
            return False
        
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.lat}&longitude={self.lon}"
                f"&current_weather=true"
                f"&hourly=temperature_2m,apparent_temperature,relativehumidity_2m,windspeed_10m,weathercode"
                f"&daily=sunrise,sunset"
                f"&timezone=auto"
                f"&forecast_days=1"
            )
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "current_weather" in data:
                cw = data["current_weather"]
                self.weather_data["temp"] = round(cw.get("temperature", 0))
                self.weather_data["windspeed"] = round(cw.get("windspeed", 0))
                self.weather_data["weather_code"] = cw.get("weathercode", 0)
                self.weather_data["condition"] = self._weather_code_to_label(
                    self.weather_data["weather_code"]
                )
                
                # Try to get more detailed hourly data
                if "hourly" in data and "time" in data["hourly"]:
                    current_time_str = cw.get("time", "")[:13] + ":00"
                    try:
                        idx = data["hourly"]["time"].index(current_time_str)
                        if "apparent_temperature" in data["hourly"]:
                            self.weather_data["feels_like"] = round(
                                data["hourly"]["apparent_temperature"][idx]
                            )
                        if "relativehumidity_2m" in data["hourly"]:
                            self.weather_data["humidity"] = round(
                                data["hourly"]["relativehumidity_2m"][idx]
                            )
                    except (ValueError, IndexError):
                        pass
                
                # Get sunrise/sunset
                if "daily" in data:
                    if "sunrise" in data["daily"] and data["daily"]["sunrise"]:
                        self.weather_data["sunrise"] = data["daily"]["sunrise"][0].split("T")[1]
                    if "sunset" in data["daily"] and data["daily"]["sunset"]:
                        self.weather_data["sunset"] = data["daily"]["sunset"][0].split("T")[1]
                
                # Get timezone
                self.timezone = data.get("timezone", None)
                
                return True
            
            return False
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return False
    
    def _weather_code_to_label(self, code):
        """Convert WMO weather code to Portuguese label"""
        if code == 0:
            return "Céu limpo"
        elif code == 1:
            return "Quase limpo"
        elif code == 2:
            return "Parc. nublado"
        elif code == 3:
            return "Nublado"
        elif code in [45, 48]:
            return "Neblina"
        elif 51 <= code <= 55:
            return "Chuvisco"
        elif 61 <= code <= 65:
            return "Chuva"
        elif 71 <= code <= 77:
            return "Neve"
        elif 80 <= code <= 82:
            return "Pancadas"
        elif code >= 95:
            return "Tempestade"
        return "Variável"
    
    def weather_code_to_category(self, code):
        """Convert weather code to simple category for rendering"""
        if code == 0:
            return "clear"
        elif code in [1, 2, 3, 45, 48]:
            return "cloudy"
        elif (51 <= code <= 67) or (80 <= code <= 82):
            return "rain"
        elif 95 <= code <= 99:
            return "storm"
        elif 71 <= code <= 77:
            return "snow"
        return "cloudy"
    
    def get_current_weather_category(self):
        """Get the current weather category for rendering"""
        code = self.weather_data.get("weather_code", 0)
        if code is not None:
            return self.weather_code_to_category(code)
        return "clear"
    
    def calculate_moon_phase(self):
        """Calculate moon phase using Jean Meeus algorithm"""
        # Reference new moon: Jan 6, 2000 18:14 UTC
        ref_date = datetime(2000, 1, 6, 18, 14)
        cycle_days = 29.53058770576
        
        now = datetime.utcnow()
        days_since = (now - ref_date).total_seconds() / 86400
        
        phase = (days_since % cycle_days) / cycle_days
        self.moon_phase = phase
        
        # Calculate illumination (0 = new, 1 = full)
        self.moon_illumination = (1 - math.cos(phase * 2 * math.pi)) / 2
        
        return phase
    
    def get_moon_emoji(self):
        """Get moon emoji based on current phase"""
        illum = self.moon_illumination
        phase = self.moon_phase
        
        if illum < 0.03:
            return "🌑"
        elif illum > 0.97:
            return "🌕"
        elif illum < 0.25:
            return "🌒" if phase < 0.5 else "🌘"
        elif illum < 0.27:
            return "🌓" if phase < 0.5 else "🌗"
        elif illum < 0.49:
            return "🌔" if phase < 0.5 else "🌖"
        elif illum < 0.51:
            return "🌕"
        elif illum < 0.74:
            return "🌔" if phase < 0.5 else "🌖"
        elif illum < 0.77:
            return "🌓" if phase < 0.5 else "🌗"
        else:
            return "🌒" if phase < 0.5 else "🌘"
