import os
import urllib.request
import subprocess

def run():
    os.makedirs("/tmp/silukman_dataset", exist_ok=True)
    
    categories = {
        "photograph": {
            "url": "https://picsum.photos/seed/{id}/256/256",
            "source": "Picsum Photos",
            "creator": "Unsplash Contributors",
            "ext": "jpg"
        },
        "flat_illustration": {
            "url": "https://robohash.org/silukman_{id}.png?set=set1&size=256x256",
            "source": "Robohash",
            "creator": "Robohash Contributors",
            "ext": "png"
        },
        "complex_illustration": {
            "url": "https://robohash.org/silukman_{id}.png?set=set2&size=256x256",
            "source": "Robohash",
            "creator": "Robohash Contributors",
            "ext": "png"
        },
        "icon": {
            "url": "https://robohash.org/silukman_{id}.png?set=set3&size=256x256",
            "source": "Robohash",
            "creator": "Robohash Contributors",
            "ext": "png"
        },
        "logo": {
            "url": "https://robohash.org/silukman_{id}.png?set=set4&size=256x256",
            "source": "Robohash",
            "creator": "Robohash Contributors",
            "ext": "png"
        }
    }

    added = 0
    for cat, meta in categories.items():
        print(f"\n--- Downloading {cat} ---")
        for i in range(12):
            url = meta["url"].format(id=i)
            tmp_path = f"/tmp/silukman_dataset/{cat}_{i}.{meta['ext']}"
            
            try:
                print(f"Downloading {url}...")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp, open(tmp_path, 'wb') as out_file:
                    out_file.write(resp.read())
            except Exception as e:
                print(f"Failed to download: {e}")
                continue
                
            cmd = [
                ".venv/bin/python", "-m", "app.cli_headless", "dataset", "add",
                "--file", tmp_path,
                "--category", cat,
                "--source-url", url,
                "--creator", meta["creator"],
                "--license", "CC0",
                "--license-url", "https://creativecommons.org/publicdomain/zero/1.0/"
            ]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Error adding {cat}_{i}: {res.stderr}")
            else:
                print(f"Added {cat}_{i}!")
                added += 1

    print(f"\nTotal added: {added}")

if __name__ == "__main__":
    run()
