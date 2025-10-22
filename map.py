import json
import csv
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import threading
import webbrowser
import time

CSV_FILE = "rock_info1.csv"  # Your CSV file


class RockServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/api/rocks":
            self.send_rock_data()
        else:
            return super().do_GET()

    def send_rock_data(self):
        try:
            rock_data = self.load_rock_data()
            json_data = json.dumps(rock_data, indent=2)

            print(f"✅ Sending {len(rock_data)} rock locations to frontend")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json_data.encode("utf-8"))

        except Exception as e:
            print(f"❌ Error serving rock data: {e}")
            self.send_error(500, "Internal Server Error")

    def load_rock_data(self):
        if os.path.exists(CSV_FILE):
            print(f"📁 Loading rock data from: {CSV_FILE}")
            return self.parse_csv_file(CSV_FILE)
        else:
            print(f"⚠️ {CSV_FILE} not found")
            return []

    def parse_csv_file(self, path):
        rock_data = []
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # auto-correct header names: lowercase + strip spaces
            headers = [h.lower().strip() for h in reader.fieldnames]
            print("🧾 CSV Headers:", headers)

            for row_num, row in enumerate(reader, start=1):
                try:
                    # auto-correct row keys to match corrected headers
                    row_lower = {k.lower().strip(): v for k, v in row.items()}

                    rock = row_lower.get("rocks", "").strip()
                    place = row_lower.get("place", "").strip()
                    rid = row_lower.get("id", str(row_num)).strip()

                    lat_str = row_lower.get("latitude", "").strip()
                    lon_str = row_lower.get("longitude", "").strip()

                    lat = float(lat_str)
                    lon = float(lon_str)

                    if not rock:
                        print(f"⚠️ Skipped row {row_num} (empty rock)")
                        continue

                    if lat == 0 or lon == 0:
                        print(f"⚠️ Skipped row {row_num} (invalid coordinates)")
                        continue

                    record = {
                        "Id": rid,
                        "Place": place,
                        "Rocks": rock,
                        "Latitude": lat,
                        "Longitude": lon
                    }

                    rock_data.append(record)
                    print(f"✅ Parsed row {row_num}: {record}")

                except Exception as e:
                    print(f"❌ Error in row {row_num}: {e}")

        print(f"🔢 Total valid rock locations: {len(rock_data)}")
        return rock_data

    def log_message(self, format, *args):
        # silence default HTTP logs
        pass

def open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:8000")

def main():
    os.chdir(os.path.dirname(__file__))
    print("🚀 Rock Finder Server running at http://localhost:8000")
    server = HTTPServer(('0.0.0.0', 8000), RockServerHandler)
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")

if __name__ == "__main__":
    main()
