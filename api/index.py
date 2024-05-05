import base64
import hashlib
import logging
import random
import string
from typing import Optional
import fastapi
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from api.clients.spotify import SpotifyClient
from api.configuration import Configuration
from templates.extension_token import EXTENSION_TOKEN_TEMPLATE


logger = logging.getLogger(__name__)
app = fastapi.FastAPI()


def generate_random_code(len: int) -> str:
    return ''.join(
        random.choices(
            string.ascii_lowercase + string.digits, k=len
        )
    )


def generate_pkce() -> tuple[str, str]:
    code_verifier = generate_random_code(128)
    code_challenge = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode().rstrip("=")

    return code_verifier, code_challenge


@app.get('/health')
async def health() -> JSONResponse:
    return JSONResponse(status_code=200, content={"status": "ok"})


@app.get("/oauth/spotify/extension/redirect")
async def spotify_extension_oauth_redirect(client_id: Optional[str] = None) -> fastapi.Response:
    configuration: Configuration = Configuration()
    redirect_uri = configuration.redirect_host + "/oauth/spotify/extension/callback"
    code_verifier, code_challenge = generate_pkce()
    scope = "+".join(configuration.spotify_scope)
    client_id = client_id or configuration.spotify_client_id

    spotify_redirect_url = (
        "https://accounts.spotify.com/authorize" +
        f"?response_type=code" +
        f"&client_id={client_id}" +
        f"&redirect_uri={redirect_uri}" +
        f"&code_challenge={code_challenge}" +
        f"&code_challenge_method=S256" + 
        f"&scope={scope}"
    )

    # Set the code verifier in a cookie
    response = RedirectResponse(url=spotify_redirect_url)
    response.set_cookie(
        "code_verifier",
        code_verifier,
        max_age=60,
        httponly=True,
        secure=False,
    )

    # Set the client_id in a cookie
    response.set_cookie(
        "client_id",
        client_id,
        max_age=60,
        httponly=True,
        secure=False,
    )

    return response


@app.get("/oauth/spotify/extension/callback")
async def spotify_extension_oauth_callback(
    request: fastapi.Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
) -> JSONResponse:
    configuration = Configuration()
    client_id = request.cookies.get("client_id")

    if not client_id:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid request",
                "error_description": "Missing client_id cookie",
            },
        )
    
    spotify_client = SpotifyClient(client_id)

    if not code and not error:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})
    
    if error or not code:
        error = error or "Invalid request"

        # If the user denied access, we should return a 400
        if error != "access_denied":
            logger.info(
                f"An error occurred during the Spotify OAuth callback: {error}",
                extra={
                    "error": error
                },
            )

        if error_description:
            error = f"{error}: {error_description}"
        
        response = JSONResponse(status_code=400, content={"error": error})
        response.delete_cookie("code_verifier")
        return response

    # Get the code verifier from the cookie
    code_verifier = request.cookies.get("code_verifier")

    if not code_verifier:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    token = await spotify_client.exchange_code_for_token(
        configuration.redirect_host + "/oauth/spotify/extension/callback",
        code,
        code_verifier,
    )

    return HTMLResponse(
        content=EXTENSION_TOKEN_TEMPLATE.substitute(token=token.refresh_token),
    )
