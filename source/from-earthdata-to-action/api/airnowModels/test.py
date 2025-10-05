import requests
import requests

url = "https://api.openaq.org/v3/sensors/3916/measurements"

headers = {
    "X-API-Key": "069f20f2bf7bdb86ecbb3371918a3c849e76039efc370d9f694d9495007eac3a"
}

params = {
    "limit": 1,
    "countries": "US"  # or "countries_id": 246 for United States
}

response = requests.get(url, headers=headers, params=params)

print("Status:", response.status_code)
print(response.json())