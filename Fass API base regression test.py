import gzip
import json
import zlib
from typing import List, Tuple

import jwt
import requests
from requests.exceptions import ContentDecodingError

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


def safe_get_json(url: str, headers: dict, timeout: int = 30):
    """
    Attempts to GET and parse JSON, handling broken gzip responses.
    Returns (status_code, json_obj, error_text)
    """
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        try:
            return res.status_code, res.json(), None
        except ValueError:
            # Not JSON
            return res.status_code, None, "Response isn't JSON"
    except ContentDecodingError as e:
        retry_headers = headers.copy()
        retry_headers["Accept-Encoding"] = "identity"
        try:
            res = requests.get(url, headers=retry_headers, timeout=timeout)
            try:
                return res.status_code, res.json(), None
            except ValueError:
                return res.status_code, None, "Response isn't JSON (after retry)"
        except Exception as e2:
            return None, None, f"Retry failed: {e2}"
    except Exception as e:
        return None, None, f"Request failed: {e}"


def call_all_endpoints_and_print(headers: dict, api: str, list_of_endpoints: List[str]):
    print(f"API address: {api}")
    print(f"--- Sending requests to {len(list_of_endpoints)} endpoints ---")
    for i, address in enumerate(list_of_endpoints):
        url = api + address
        status, j_res, err = safe_get_json(url, headers)
        outp = (
            f"[{i+1}] {''.join([' ']*(2-len(str(i+1))))}"
            f"{address.split('=')[0]:<{78}}"
        )

        if status is None:
            outp += "\033[91mERR\033[0m"
            print(outp)
            print(f"\t- {err}")
            continue

        if j_res is None:
            # Either non-JSON or retry failure
            color = "\033[92m" if (200 <= status < 300) else "\033[91m"
            outp += f"{color}{status}\033[0m"
            print(outp)
            if err:
                print(f"\t- {err}")
            continue

        if status >= 400:
            outp += f"\033[91m{status}\033[0m"
            errs = j_res.get("validationErrors")
            if errs:
                outp += f"\n\t- {errs[0].get('text')}"
        else:
            outp += f"\033[92m{status}\033[0m"

        print(outp)


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


def main():
    # username = "vabuser"
    # password = "FH-Tb46_H$*g2VCj"

    # username = "test_vet_access"
    # password = "testTest123!!"

    username = "clga_test"
    password = "!testTest123!"

    env_prefix = "ACC"

    try:
        jwt = authenticate(env_prefix, username, password)
        # jwt = "eyJraWQiOiJlMlN4eWJUMVJmNytkOU85NjZmdnFGVkI2MjRna0RWNks5dVRhcmFRR3pNPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIwMjYyNWQ4My0zMjAwLTRjODgtYTA2YS03OThiNmVlMmY1YzciLCJjb2duaXRvOmdyb3VwcyI6WyJGVUxMLUFDQ0VTUyJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtbm9ydGgtMS5hbWF6b25hd3MuY29tXC9ldS1ub3J0aC0xX1VzaDFLSHcwZyIsImNsaWVudF9pZCI6IjE3MGpiN2lqMzJycmM1bmNnMHE2MDBvbGtuIiwiZXZlbnRfaWQiOiI3YWQ5ZDQ3MS04NDQ2LTQ1ZjMtYjQ0Mi04MDk2MzY4ZmM2NGYiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIiwiYXV0aF90aW1lIjoxNzExMzY4NDE0LCJleHAiOjE3MTEzNzIwMTQsImlhdCI6MTcxMTM2ODQxNCwianRpIjoiYzczODA2ZTMtMTZlMS00ZmIwLThmYzMtODRhNGYyNzViODAyIiwidXNlcm5hbWUiOiJ2YWJ1c2VyIn0.XOkCZogELtk6rlN8sZM6DYzjXl436tggjIRW3RJyG1e0H-t7zDZgn4QM1zobk2yXQ1mLO1dvhcHo-ZUIDn68bfOjwqNn2-9WIcOz0qjWncQmQMeM3aJTdFGFU-_MBoX4nrnkar9XH_dxcnmbFW89wH0LsOCei75EU4bIMCGbagA2gQPdZRQ76YUN_rANuJ0aa2G5IQnZIre5yVHOWYjJ0GStzSdQvYBfN8Muw_mX1oobHQkmt21ug4seQKrkNrR2ME9PXcky08p45YNqRW7fjD3P15uZ7MK0paD9CHLDFafBr8x9DhGoDI6lJu0gOiuFXFeZ0JmIy9SINOZ280W2hQ"
    except:
        print("Script exited prematurely")
        exit()

    print_decoded_jwt(jwt)

    header = {"Authorization": f"Bearer {jwt}"}
    print(f"\n--- Human API---")
    call_all_endpoints_and_print(
        header, globals()[f"{env_prefix}_API"], human_endpoints
    )

    print(f"\n--- VET API---")
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_VET_API"], human_endpoints)
    call_all_endpoints_and_print(
        header, globals()[f"{env_prefix}_VET_API"], vet_endpoints
    )

    print(f"\n--- VAB---")
    header["Accept"] = "application/fassapi-v1+json"
    header["Content-Type"] = "application/json"
    header["x-timestamp"] = "1666245919202"
    header["x-authentication-hash"] = "c5858c6bd55afc8713aa059188191dc5"
    header["x-correlation-id"] = "41bd324"
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_VAB"], human_endpoints)
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_VAB"], vet_endpoints)
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_VAB"], vab_endpoints)

    print(f"\n--- DAB---")
    header["x-timestamp"] = "1694425530628"
    header["x-authentication-hash"] = (
        "a90ba19bef5ea0d510168d94295e83fc11404df8b14ac765fe1c7028e7fc2433"
    )
    header["x-correlation-id"] = "5896487"
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_DAB"], human_endpoints)
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_DAB"], vet_endpoints)
    call_all_endpoints_and_print(header, globals()[f"{env_prefix}_DAB"], dab_endpoints)


if __name__ == "__main__":
    main()
