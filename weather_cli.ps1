<#
.SYNOPSIS
  Prompts for a city, then fetches current temperature and weather using Open-Meteo (free, no API key).
  Compare with your sky simulation's weather.
#>

$ErrorActionPreference = "Stop"
$City = Read-Host "City"
if (-not $City) { $City = "São Paulo" }

$api = "https://geocoding-api.open-meteo.com/v1/search"
$query = "?name=$([System.Uri]::EscapeDataString($City))&count=1&language=en&format=json"

try {
  $geo = Invoke-RestMethod -Uri "$api$query" -Method Get
  if (-not $geo.results -or $geo.results.Count -eq 0) {
    Write-Host "City not found: $City" -ForegroundColor Red
    exit 1
  }

  $lat = $geo.results[0].latitude
  $lon = $geo.results[0].longitude
  $name = $geo.results[0].name
  $country = $geo.results[0].country

  $weather = Invoke-RestMethod -Uri "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code&timezone=auto" -Method Get

  $c = $weather.current
  $time = [datetime]::Parse($c.time)

  $codes = @{
    0  = "Clear"; 1 = "Mainly clear"; 2 = "Partly cloudy"; 3 = "Overcast"
    45 = "Fog"; 48 = "Depositing rime fog"
    51 = "Light drizzle"; 53 = "Moderate drizzle"; 55 = "Dense drizzle"
    61 = "Slight rain"; 63 = "Moderate rain"; 65 = "Heavy rain"
    71 = "Slight snow"; 73 = "Moderate snow"; 75 = "Heavy snow"
    80 = "Slight showers"; 81 = "Moderate showers"; 82 = "Violent showers"
    95 = "Thunderstorm"; 96 = "Thunderstorm with slight hail"; 99 = "Thunderstorm with heavy hail"
  }
  $desc = if ($codes.ContainsKey($c.weather_code)) { $codes[$c.weather_code] } else { "Unknown" }

  Write-Host ""
  Write-Host "  $name, $country" -ForegroundColor Cyan
  Write-Host "  $($time.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
  Write-Host ""
  Write-Host "  Temperature:      $($c.temperature_2m)°C" -ForegroundColor Yellow
  Write-Host "  Feels like:       $($c.apparent_temperature)°C" -ForegroundColor Yellow
  Write-Host "  Humidity:         $($c.relative_humidity_2m)%" -ForegroundColor Green
  Write-Host "  Conditions:       $desc" -ForegroundColor White
  Write-Host ""
}
catch {
  Write-Host "Error fetching weather: $_" -ForegroundColor Red
  exit 1
}
