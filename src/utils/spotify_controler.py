import requests
import json


class SpotifyControler:
    TOKEN_URL = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
    CURRENT_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
    LYRICS_URL = "https://spclient.wg.spotify.com/color-lyrics/v2/track/"

    def __init__(self, cookies=""):
        self.cookies = cookies
        self.token = ""

    def loadAccessToken(self, cookies=""):
        h = {
            "referer": "https://open.spotify.com/",
            "origin": "https://open.spotify.com/",
            "accept": "application/json",
            "accept-language": "en",
            "app-platform": "WebPlayer",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "spotify-app-version": "1.1.87.0-unknown",
            "cookie": cookies if cookies != "" else self.cookies,
        }
        try:
            req = requests.get(SpotifyControler.TOKEN_URL, headers=h)
        except:
            return False
        self.token = json.loads(req.text)["accessToken"]
        return True

    def getHeaders(self):
        headers = {
            "accept": "application/json",
            "accept-Language": "en",
            "origin": "https://open.spotify.com",
            "referer": "https://open.spotify.com/",
            "app-platform": "WebPlayer",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua": 'Chromium";v="100", " Not A;Brand";v="99"',
            "sec-ch-ua-platform": "Windows",
            "spotify-app-version": "1.1.87.0-unknown",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.162 Safari/537.36",
            "authorization": "Bearer " + self.token,
        }
        return headers

    def getCurrentlyPlaying(self):
        headers = self.getHeaders()
        response = requests.get(SpotifyControler.CURRENT_PLAYING_URL, headers=headers)
        try:
            return json.loads(response.text)
        except:
            return response.text

    def getLyrics(self, idSong):
        url = f"{SpotifyControler.LYRICS_URL}{idSong}/"
        headers = self.getHeaders()
        req = requests.get(url, headers=headers)
        try:
            return json.loads(req.text)
        except:
            return req.text
