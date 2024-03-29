import os


class Configuration:
    def __init__(self) -> None:
        self.spotify_client_id: str = "c47877614f4e4632b293a40fe7a260e2"
        self.spotify_scope: list[str] = [ 'user-modify-playback-state', 'user-read-playback-state' ]
        self.redirect_host: str = os.getenv("REDIRECT_HOST", "http://localhost:3000")
