import requests

url = 'http://gibt/api/crawler/characters'

r = requests.get(url)
if(r.status_code == 200):
    text = r.text
    print(text)
else:
    print(r.status_code)