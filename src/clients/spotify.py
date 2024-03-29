from typing import Optional, Union
import httpx
from pydantic import BaseModel


class OAuthToken(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] 
    scope: Union[list[str], str]
    token_type: str


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
    ) -> None:
        self.client_id = client_id
        self.client = httpx.AsyncClient()
    
    async def exchange_code_for_token(self, redirect_uri: str, code: str, code_verifier: str) -> OAuthToken:
        url = "https://accounts.spotify.com/api/token"
        data = {
            "client_id": self.client_id,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            'code_verifier': code_verifier
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )

            response.raise_for_status()
            return OAuthToken(**response.json())
