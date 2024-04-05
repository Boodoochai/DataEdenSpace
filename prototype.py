import requests

URL = "https://datsedenspace.datsteam.dev"

AUTH_TOKEN = "66043a4c2b79766043a4c2b79a"

response = requests.get(URL + '/player/universe', headers={"X-Auth-Token": AUTH_TOKEN})

print(response.status_code)
print(response.json())

# payload = {"planets": ["Roob-43"]}
#
# response = requests.post(URL + '/player/travel', json=payload, headers={"X-Auth-Token": AUTH_TOKEN})
#
# print(response.json())
