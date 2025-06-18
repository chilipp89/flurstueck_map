import json

import folium as folium
import requests as requests
import pandas as pd


def find_flurstueck(gemarkung: int, flurnummer: int, flurstueck: int, flurstueck_nenner: int = None):
    base_url = "https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/flstk_hessen/FeatureServer/0/query?where=gemarkung_AX_Gemarkung_Schluess%20%3D%20'{gemarkung}'%20AND%20flurstuecksnummer_AX_Flurstueck%20%3D%20'{flurstueck}'&outFields=*&outSR=4326&f=json"
    base_url_nenner = "https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/flstk_hessen/FeatureServer/0/query?where=gemarkung_AX_Gemarkung_Schluess%20%3D%20'{gemarkung}'%20AND%20flurstuecksnummer_AX_Flurstueck%20%3D%20'{flurstueck}'%20AND%20flurstuecksnummer_AX_Flurstue_1%20%3D%20'{flurstueck_nenner}'&outFields=*&outSR=4326&f=json"
    if flurstueck_nenner is None:
        request_url = base_url.format(gemarkung=gemarkung, flurstueck=flurstueck)
    else:
        request_url = base_url_nenner.format(gemarkung=gemarkung, flurstueck=flurstueck,
                                             flurstueck_nenner=flurstueck_nenner)
    resp = requests.get(request_url)
    geojson = resp.json()
    features = [entry for entry in geojson["features"] if entry["attributes"]["flurnummer"] == flurnummer]

    if len(features) == 1:
        return features[0]
    if len(features) == 0:
        return None
    else:
        raise ValueError("Kein Flurstueck gefunden")


def plot_map(data):
    # Get a central point to center the map (using the first coordinate)
    first_ring = data[0]['geometry']['rings'][0]
    center_lat = sum([pt[1] for pt in first_ring]) / len(first_ring)
    center_lon = sum([pt[0] for pt in first_ring]) / len(first_ring)

    # Create a map with satellite basemap
    m = folium.Map(location=[center_lat, center_lon], zoom_start=17,
                   tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                   attr='Map data © OpenStreetMap contributors')

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

            flurstueck_name = feature['attributes']['flurstuecksnummer_AX_Flurstueck']
            if feature['attributes']['flurstuecksnummer_AX_Flurstue_1']:
                flurstueck_name = f"{feature['attributes']['flurstuecksnummer_AX_Flurstueck']}/{feature['attributes']['flurstuecksnummer_AX_Flurstue_1']}"

            folium.Polygon(
                locations=polygon,
                color='blue',
                weight=2,
                fill=True,
                fill_opacity=0.3,
                popup=f"""<p>Flur: {feature['attributes']['flurnummer']} </br> 
                          Flurstueck: {flurstueck_name} </br>  
                          Flaeche: {feature['attributes']['amtlicheFlaeche']/10000} ha  </br></p> """
            ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # JavaScript: Properly trigger geolocation on button click
    locate_me_js = """
    <script>
    document.addEventListener("DOMContentLoaded", function () {
        // Locate Leaflet map instance
        var map;
        for (var key in window) {
            if (window[key] instanceof L.Map) {
                map = window[key];
                break;
            }
        }
        if (!map) return;

        // Add Locate button
        var locateBtn = L.control({position: 'topleft'});
        locateBtn.onAdd = function () {
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            var btn = L.DomUtil.create('a', '', div);
            btn.innerHTML = '📍';
            btn.title = 'Locate Me';
            btn.href = '#';
            btn.style.width = '30px';
            btn.style.height = '30px';
            btn.style.fontSize = '18px';
            btn.style.lineHeight = '30px';
            btn.style.background = 'white';
            btn.style.textAlign = 'center';
            btn.onclick = function (e) {
                e.preventDefault();
                if (!navigator.geolocation) {
                    alert("Geolocation is not supported by your browser.");
                    return;
                }
                navigator.geolocation.getCurrentPosition(function (pos) {
                    var latlng = [pos.coords.latitude, pos.coords.longitude];
                    var accuracy = pos.coords.accuracy;

                    // Remove previous marker
                    if (window.currentMarker) map.removeLayer(window.currentMarker);
                    if (window.currentCircle) map.removeLayer(window.currentCircle);

                    window.currentMarker = L.marker(latlng).addTo(map)
                        .bindPopup("You are here").openPopup();
                    window.currentCircle = L.circle(latlng, {radius: accuracy}).addTo(map);

                    map.setView(latlng, 18);
                }, function (err) {
                    alert("Geolocation error: " + err.message);
                });
            };
            return div;
        };
        locateBtn.addTo(map);
    });
    </script>
    """

    # Inject JS
    m.get_root().html.add_child(folium.Element(locate_me_js))

    # Save to HTML file
    m.save("map_with_geometry.html")


if __name__ == "__main__":

    # df = pd.read_excel(r"C:\Users\phi-j\OneDrive\Dokumente\UmbauAmoeneburg\Hofübergabe\Hofübergabe.xlsx", "Flurstuecke")
    #
    # flurstueck_info = []
    # for _, row in df.iterrows():
    #     gemarkung = int(row["Gemarkung"])
    #     flurnummer = int(row["Flur"])
    #     flurstueck = int(row["Flurstück"])
    #     flurstueck_nenner = row["Flurstück_Nenner"]
    #     if pd.isna(flurstueck_nenner):
    #         flurstueck_nenner = None
    #     else:
    #         flurstueck_nenner = int(flurstueck_nenner)
    #     flurstueck_info.append(find_flurstueck(gemarkung, flurnummer, flurstueck, flurstueck_nenner))

    with open('data2.json', 'r') as f:
        flurstueck_info = json.load(f)

    plot_map(flurstueck_info)

    print("test")

