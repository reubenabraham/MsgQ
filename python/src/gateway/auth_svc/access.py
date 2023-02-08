import os, requests
import logging

log = logging.getLogger(f"{__name__}.sub")

def login(request):
    log.warning("We're in login")
    log.warning(f"Request: {request}")
    auth = request.authorization
    log.warning(f"Auth:{auth}")
    if not auth:
        log.warning("In not auth")
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)
    log.warning(f"{basicAuth}: {auth.username} , {auth.password}")

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login", auth=basicAuth
    )
    log.warning(f"Response code: {response}")

    if response.status_code == 200:
        log.warning("Successful response")
        return response.text, None
    else:
        log.warning("Unsuccessful response")
        return None, (response.text, response.status_code)