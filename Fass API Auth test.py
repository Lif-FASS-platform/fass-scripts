import json
from typing import List, Tuple

import jwt
import requests

from api_gateway_groups import endpoints

API = "https://test-api.fass.se"
VET_API = "https://test-vetapi.fass.se"

test_endpoints: List[Tuple[str]] = [
    ("UNAUTHORIZED", API + "/alive"),
    ("E-HEALTH-AGENCY", API + "/custom/ehm/indication/20000225000063"),
    ("HUMAN", API + "/atc/top-level"),
    ("VETERINARY", VET_API + "/atc/top-level"),
    ("FULL_ACCESS", API + "/cities?countyCode=2"),
    ("SOLID_DOSAGE_FORM", API + "/medical-device/all?number=1"),
    (
        "ENVIRONMENTAL_INFORMATION_READY_FOR_REVIEW (IVL)",
        API
        + "/fass-environmental-information-ready-for-review/changelog?timestamp=2023-09-09",
    ),
]


def authenticate(username: str, password: str) -> str:
    # Authenticates to Fass API and returns a JWT
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/json"}
    print(f"Authenticating to {API}..")
    res = requests.post(API + "/login", headers=headers, json=payload)

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


def main():
    # username = "clga_test"
    # password = "!testTest123!"
    username = "dabuser"
    password = "FH-Tb46_H$*g2VCj"

    try:
        jwt = authenticate(username, password)
    except:
        print("Script exited prematurely")
        exit()

    print_decoded_jwt(jwt)

    headers = {"Authorization": f"Bearer {jwt}"}
    print(f"--- Sending requests to {len(endpoints)} endpoints ---")
    for i, (address, roles) in enumerate(endpoints.items()):
        try:
            res = requests.get(API + address, headers=headers)
        except:
            print(f"Couldn't connect to {address}")
            continue
        try:
            j_res = res.json()
        except:
            print(f"Response from {address} isn't json")
            # print(res.text)
            continue

        outp = (
            f"[{i+1}] {''.join([' ']*(3-len(str(i+1))))}"
            f"{address.split('=')[0]:<{78}}"
        )

        if res.status_code >= 400:
            outp += f"{j_res.get('statusCode')} {j_res.get('status')}"
            outp += f"\033[91m{res.status_code}\033[0m"
            errs = j_res.get("validationErrors")
            if errs:
                outp += f"\n\t- {errs[0].get('text')}"
        else:
            outp += f"\033[92m{res.status_code}\033[0m"

        print(outp)


if __name__ == "__main__":
    main()
