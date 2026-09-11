import urllib.request
import re

html = urllib.request.urlopen('https://railmadad.indianrailways.gov.in/madad/final/home.jsp').read().decode('utf-8')
ids = re.findall(r'id="([^"]+)"', html)
for id in ids:
    print(id)
