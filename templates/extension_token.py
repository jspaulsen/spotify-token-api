from string import Template


EXTENSION_TOKEN_TEMPLATE = Template(
    """
    <html>
    <head>
        <title>Spotify Extension Token</title>
    </head>
    <body>
        <h1>Spotify Extension Token</h1>
        <p>
            <br>
                Your Spotify extension token is: <strong>$token</strong>
            </br>
            <br>
                When you close this window, add this token to the prompt in Sammi.
            </br>
        </p>
    """
)
