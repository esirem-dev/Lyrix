import requests
import json
import pathlib
import os


class BPM:
    URL_BASE = "https://bpm-searcher.onrender.com/api/v1/track"

    def __init__(self):
        self.data = {}

        self._load_data()

    def _load_data(self):
        save_path = pathlib.Path(__file__).parent.parent / "cache" / "bpm.json"
        if save_path.exists():
            with open(save_path, "r") as f:
                self.data = json.load(f)
        else:
            os.makedirs(save_path.parent, exist_ok=True)
            self.data = {}
            with open(save_path, "w") as f:
                json.dump(self.data, f)

    def _save_data(self):
        save_path = pathlib.Path(__file__).parent.parent / "cache" / "bpm.json"
        with open(save_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def _add_data(self, artist, title, bpm):
        self.data[f"{artist} {title}"] = bpm
        self._save_data()

    def _get_data(self, artist, title):
        if f"{artist} {title}" in self.data:
            return self.data[f"{artist} {title}"]
        return None

    def _get_bpm(self, artist, title):
        try:
            url = f"{BPM.URL_BASE}?search={artist} {title}"
            url = url.replace(" ", "%20")
            response = requests.get(url)

            if response.status_code == 200:
                data = json.loads(response.text)
                artist = data[0]["artist"]
                title = data[0]["song_name"]
                bpm = data[0]["bpm"]
                print(f"{artist} - {title} : {bpm}")
                return bpm
            else:
                return None
        except:
            return None

    def _simplify(self, x):
        x = x.replace("&", "")
        return x

    def get_bpm(self, artist, title):
        artist = self._simplify(artist)
        title = self._simplify(title)
        bpm = self._get_data(artist, title)
        if bpm is None:
            bpm = self._get_bpm(artist, title)
            if bpm is not None:
                self._add_data(artist, title, bpm)
            else:
                return None
        return bpm


if __name__ == "__main__":
    bpm = BPM()
    print(bpm.get_bpm("Orelsan", "Manifest"))
    print(bpm.get_bpm("Orelsan", "Discipline"))
