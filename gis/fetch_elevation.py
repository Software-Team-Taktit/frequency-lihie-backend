import requests, re, time, csv
from pathlib import Path

CITIES_PATH = Path(__file__).parent / "cities.txt"
OUT_CSV     = Path(__file__).parent / "cities_elevation.csv"
NOT_FOUND   = Path(__file__).parent / "not_found.txt"

UA = {"User-Agent": "Merhavim-GIS/1.0 (contact: you@example.com)"}
NOMI = "https://nominatim.openstreetmap.org/search"
ELEV = "https://api.open-elevation.com/api/v1/lookup"

GAZA_HINTS = ["עזה","רפיח","חאן יונס","דיר אל-בלח","ג'באליה","בית לאהיה"]
WB_HINTS   = ["חברון","בית לחם","רמאללה","שכם","ג'נין","קלקיליה","טול כרם","יריחו",
              "מודיעין עילית","ביתר עילית","מעלה אדומים","אריאל","אל-בירה","סלפית","טובאס"]

def clean_name(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", s)       
    s = s.split(" - ")[0]              
    s = s.replace("–", "-").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def query_variants(name: str):
    base = clean_name(name)
    if any(h in base for h in GAZA_HINTS):
        return [f"{base}, Gaza Strip", base]
    if any(h in base for h in WB_HINTS):
        return [f"{base}, West Bank", base, f"{base}, Palestine"]
    return [f"{base}, Israel", base]

def pick_best(arr):
    if not arr: return None
    def score(x):
        cls = x.get("class"); typ = x.get("type")
        place_rank = 0
        if cls == "place" and typ in {"city","town","village","hamlet","suburb","neighbourhood"}:
            place_rank = 3
        elif cls == "boundary" or typ == "administrative":
            place_rank = 2
        elif x.get("geojson"):
            place_rank = 1
        cc = (x.get("address",{}) or {}).get("country_code","")
        cc_bonus = 1 if cc in {"il","ps"} else 0
        return (place_rank, cc_bonus, float(x.get("importance",0)))
    return sorted(arr, key=score, reverse=True)[0]

def search_city(name: str):
    tried = []
    for q in query_variants(name):
        params = {"q": q, "format": "json", "limit": 5, "addressdetails": 1, "accept-language": "he", "countrycodes": "il,ps"}
        r = requests.get(NOMI, params=params, headers=UA, timeout=40)
        if r.ok:
            arr = r.json()
            best = pick_best(arr)
            if best:
                return float(best["lat"]), float(best["lon"]), best
        tried.append(q)
        time.sleep(1.2)
    return None, None, {"tried": tried}

def get_elevation(lat, lon):
    r = requests.get(ELEV, params={"locations": f"{lat},{lon}"}, timeout=40)
    r.raise_for_status()
    return float(r.json()["results"][0]["elevation"])

def main():
    cities = [line.strip() for line in CITIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    ok_rows, misses = [], []

    for i, name in enumerate(cities, 1):
        try:
            lat, lon, meta = search_city(name)
            if lat is None:
                misses.append(name)
                print(f"[{i}] ❌ לא נמצא: {name}")
                continue
            elev = get_elevation(lat, lon)
            ok_rows.append({"city": clean_name(name), "latitude": lat, "longitude": lon, "elevation_m": elev})
            print(f"[{i}] ✓ {clean_name(name)} → ({lat:.5f},{lon:.5f}) elev={elev}")
            time.sleep(0.8) 
        except Exception as e:
            misses.append(name)
            print(f"[{i}] ✗ שגיאה ב-{name}: {e}")
            time.sleep(1.5)

    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["city","latitude","longitude","elevation_m"])
        w.writeheader(); w.writerows(ok_rows)
    NOT_FOUND.write_text("\n".join(misses), encoding="utf-8")

    print(f"\n✅ נשמר {OUT_CSV} ({len(ok_rows)} רשומות)")
    print(f"⚠️ לא נמצאו {len(misses)} שמות → ראי {NOT_FOUND}")

if __name__ == "__main__":
    main()
