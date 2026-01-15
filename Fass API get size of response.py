import json
from typing import List, Tuple

import jwt
import requests

from endpoints import dab_endpoints, human_endpoints, vab_endpoints, vet_endpoints

# SYSTEST
SYS_API = "https://api.fass.systest.dev.fass.se"
SYS_VET_API = "https://vetapi.fass.systest.dev.fass.se"
SYS_VAB = "https://vab.fass.systest.dev.fass.se"
SYS_DAB = "https://dab.fass.systest.dev.fass.se"

# ACCTEST
ACC_API = "https://test-api.fass.se"
ACC_VET_API = "https://test-vetapi.fass.se"
ACC_VAB = "https://test-vab.fass.se"
ACC_DAB = "https://test-dab.fass.se"


def authenticate(env: str, username: str, password: str) -> str:
    # Authenticates to Fass API and returns a JWT
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/json"}
    print(f"Authenticating to {globals()[f'{env}_API']}..")
    res = requests.post(
        globals()[f"{env}_API"] + "/login", headers=headers, json=payload
    )

    if res.status_code >= 400:
        print(f"Failed to authenticate")
        print(res.status_code, res.reason)
        raise

    try:
        token = res.json()["jwtToken"]
        print("Authentication successful!")
        return token

    except KeyError:
        print(f"Couldn't fetch JWT token from response body: {res.json()}")
        raise


def print_decoded_jwt(token: str):
    decoded_data = jwt.decode(
        jwt=token, options={"verify_signature": False}, algorithms=["RS256"]
    )
    # print(json.dumps(decoded_data, sort_keys=True, indent=2))
    u = decoded_data.get("username") or decoded_data.get("sub")
    g = decoded_data.get("cognito:groups") or decoded_data.get("authorities")
    print(f"user: {u}, " f"member of groups: {g}")


def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size,2)}{power_labels[n] + 'b'}"


def call_all_endpoints_and_print(headers: str, api: str, list_of_endpoints: List[str]):
    print(f"--- Sending requests to {len(list_of_endpoints)} endpoints ---")
    for i, address in enumerate(list_of_endpoints):
        res = requests.get(api + address, headers=headers)
        if res.status_code >= 400 and "number" in address:
            res = requests.get(api + address[:-3] + "200", headers=headers)
            if res.status_code >= 400:
                res = requests.get(api + address[:-3] + "100", headers=headers)
        try:
            print_response(i, res, address)
        except:
            continue


def print_response(i, res, address):
    size = format_bytes(len(res.content))
    outp = (
        f"[{i+1}] {size:<{8}} {''.join([' ']*(2-len(str(i+1))))}"
        f"{address.split('=')[0]:<{74}}"
    )

    try:
        j_res = res.json()
    except:
        outp += f"\033[91m{res.status_code}\033[0m"
        print(outp)
        print(f"Response isn't json")

    if res.status_code >= 400:
        # outp += f"{j_res.get('statusCode')} {j_res.get('status')}"
        outp += f"\033[91m{res.status_code}\033[0m"
        errs = j_res.get("validationErrors")
        if errs:
            outp += f"\n\t- {errs[0].get('text')}"
    else:
        outp += f"\033[92m{res.status_code}\033[0m"

    print(outp)


def main():
    # username = "vabuser"
    # password = "FH-Tb46_H$*g2VCj"
    username = "clga_test"
    password = "!testTest123!"
    env_prefix = "SYS"

    try:
        jwt = authenticate(env_prefix, username, password)
    except:
        print("Couldn't authenticate")
        exit()

    print_decoded_jwt(jwt)

    headers = {"Authorization": f"Bearer {jwt}"}
    print(f"\n--- Human API ---")
    call_all_endpoints_and_print(
        headers, globals()[f"{env_prefix}_API"], human_endpoints
    )

    print(f"\n--- VET API ---")
    # call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_VET_API"], human_endpoints)
    call_all_endpoints_and_print(
        headers, globals()[f"{env_prefix}_VET_API"], vet_endpoints
    )

    print(f"\n--- VAB ---")
    headers["Accept"] = "application/fassapi-v1+json"
    headers["Content-Type"] = "application/json"
    headers["x-timestamp"] = "1666245919202"
    headers["x-authentication-hash"] = "c5858c6bd55afc8713aa059188191dc5"
    headers["x-correlation-id"] = "41bd324"
    # call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_VAB"], human_endpoints)
    # call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_VAB"], vet_endpoints)
    call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_VAB"], vab_endpoints)

    print(f"\n--- DAB ---")
    headers["x-timestamp"] = "1694425530628"
    headers["x-authentication-hash"] = (
        "a90ba19bef5ea0d510168d94295e83fc11404df8b14ac765fe1c7028e7fc2433"
    )
    headers["x-correlation-id"] = "5896487"
    # call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_DAB"], human_endpoints)
    # call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_DAB"], vet_endpoints)
    call_all_endpoints_and_print(headers, globals()[f"{env_prefix}_DAB"], dab_endpoints)


if __name__ == "__main__":
    main()
