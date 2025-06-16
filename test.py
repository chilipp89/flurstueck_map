import json
import folium

# Load the data
with open("data.json", "r") as f:
    data = json.load(f)

# Get a central point to center the map (using the first coordinate)
first_ring = data[0]['geometry']['rings'][0]
center_lat = sum([pt[1] for pt in first_ring]) / len(first_ring)
center_lon = sum([pt[0] for pt in first_ring]) / len(first_ring)

# Create a map with satellite basemap
m = folium.Map(location=[center_lat, center_lon], zoom_start=17, tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr='Map data © OpenStreetMap contributors')

# Add Esri Satellite basemap (optional alternative)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri Satellite',
    overlay=False,
    control=True
).add_to(m)

# Plot each geometry
for feature in data:
    rings = feature['geometry']['rings']
    for ring in rings:
        polygon = [(latlng[1], latlng[0]) for latlng in ring]  # folium expects (lat, lon)
        folium.Polygon(
            locations=polygon,
            color='blue',
            weight=2,
            fill=True,
            fill_opacity=0.3,
            popup=f"ID: {feature['attributes']['OBJECTID']}"
        ).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

locate_js = """
<script>
navigator.geolocation.getCurrentPosition(
    function(position) {
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;
        var accuracy = position.coords.accuracy;

        var marker = L.marker([lat, lon]).addTo(window.map);
        marker.bindPopup("You are here").openPopup();

        var circle = L.circle([lat, lon], {radius: accuracy}).addTo(window.map);
    },
    function(error) {
        alert("Geolocation failed: " + error.message);
    }
);
</script>
"""

# Attach JS to map
m.get_root().html.add_child(folium.Element(locate_js))


# Save to HTML file
m.save("map_with_geometry.html")