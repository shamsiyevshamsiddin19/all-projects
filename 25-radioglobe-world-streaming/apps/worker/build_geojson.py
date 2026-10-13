import json
import urllib.request
from pathlib import Path

def round_coords(geom, precision=3):
    if not geom:
        return geom
    coords = geom.get("coordinates")
    if not coords:
        return geom
    
    def _round(c):
        if isinstance(c, (int, float)):
            return round(c, precision)
        if isinstance(c, (list, tuple)):
            return [_round(x) for x in c]
        return c

    geom["coordinates"] = _round(coords)
    return geom

def build_geojson():
    url = "https://raw.githubusercontent.com/datasets/geo-boundaries-world-110m/master/countries.geojson"
    print(f"Downloading boundaries from {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "RadioGlobe/1.0"})
    with urllib.request.urlopen(req) as resp:
        raw_data = json.loads(resp.read().decode("utf-8"))

    print(f"Raw features count: {len(raw_data.get('features', []))}")

    # Optimize and normalize features
    features = []
    for f in raw_data.get("features", []):
        props = f.get("properties", {})
        iso_a2 = props.get("iso_a2", "")
        iso_a3 = props.get("iso_a3", "")
        name = props.get("name", "")

        # Fix -99 for France, Norway, etc.
        if iso_a2 == "-99" or not iso_a2:
            if iso_a3 == "FRA": iso_a2 = "FR"
            elif iso_a3 == "NOR": iso_a2 = "NO"
            elif iso_a3 == "XKX": iso_a2 = "XK"

        geom = round_coords(f.get("geometry", {}), precision=3)
        
        feature = {
            "type": "Feature",
            "id": iso_a2 or iso_a3 or name,
            "properties": {
                "iso2": iso_a2,
                "iso3": iso_a3,
                "name_en": name,
                "name_uz": name,
                "radio_count": 0,
                "tv_count": 0
            },
            "geometry": geom
        }
        features.append(feature)

    output = {
        "type": "FeatureCollection",
        "features": features
    }

    out_api = Path(__file__).resolve().parent.parent / "api" / "data" / "countries.geojson"
    out_web = Path(__file__).resolve().parent.parent / "web" / "public" / "countries.geojson"

    out_api.parent.mkdir(parents=True, exist_ok=True)
    out_web.parent.mkdir(parents=True, exist_ok=True)

    with open(out_api, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))

    with open(out_web, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(',', ':'))

    file_size_kb = out_api.stat().st_size / 1024
    print(f"GeoJSON successfully generated! Size: {file_size_kb:.1f} KB")

if __name__ == "__main__":
    build_geojson()
