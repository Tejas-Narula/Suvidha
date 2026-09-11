import urllib.request
import re

try:
    html = urllib.request.urlopen('https://railmadad.indianrailways.gov.in/madad/final/home.jsp').read().decode('utf-8')
    # Find all <input ...> tags
    inputs = re.findall(r'<input[^>]+>', html)
    print("Found", len(inputs), "inputs")
    for inp in inputs:
        # Extract id and placeholder
        id_match = re.search(r'id=["\']([^"\']+)["\']', inp)
        ph_match = re.search(r'placeholder=["\']([^"\']+)["\']', inp)
        type_match = re.search(r'type=["\']([^"\']+)["\']', inp)
        
        id_str = id_match.group(1) if id_match else "None"
        ph_str = ph_match.group(1) if ph_match else "None"
        type_str = type_match.group(1) if type_match else "None"
        
        print(f"ID: {id_str} | Placeholder: {ph_str} | Type: {type_str}")
except Exception as e:
    print("Error:", e)
