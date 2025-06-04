import time
import json
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def extract_token(response):
    """
    Extracts the access token from an HTTP response object.

    :param response: An HTTP response object containing JSON data with an access token.
    :return: The access token as a string if present, otherwise None.
    """
    response_text = response.content.decode("utf-8")
    response_json = json.loads(response_text)
    return response_json.get("access_token", None)


def get_token(username, password):
    """
    Authenticates the user by sending their username and password
    to a token endpoint, and retrieves an access token if successful.

    :param username: The username of the user attempting to authenticate.
    :param password: The password of the user attempting to authenticate.
    :return: An access token if authentication is successful; otherwise, None.
    """
    url = "https://fei-nu211/api/v1/token"
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
    response = requests.post(url, data=data, headers=headers, verify=False)
    if response.status_code == 200:
        return extract_token(response)
    else:
        print(f"Failed to retrieve token: {response.status_code}")
        print("Response Body:", response.text)
        return None


def process_iv_data(response, curve="A"):
    """
    Processes IV data from a response object and returns it as a DataFrame.

    :param response: A dictionary containing the response data.
                     The data is expected to be nested under response["results"][0]["results"].
    :param curve: A string representing the curve name to extract the data for.
                  Defaults to "A". Only "A" and "B" possible.
    :return: A pandas DataFrame with columns "Current (I)" and "Voltage (V)".
             The "Current (I)" column contains current values extracted from the data,
             and the "Voltage (V)" column contains voltage values.
    """
    data = response["results"][0]["results"][curve]
    current = [point["i"] for point in data]
    voltage = [point["v"] for point in data]
    return pd.DataFrame({"Current (I)": [current], "Voltage (V)": [voltage]})


def poll_ivcurve_status(token):
    """
    Polls the IV curve status from a remote server until the job is complete.

    :param token: Authentication token required for accessing the API.
    :return: Processed IV data if the job is complete, None if there's an error in response.
    """
    url = "https://fei-nu211/api/v1/ivcurve/latestJob"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    while True:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "DONE":
                print("Measurement complete.")
                try:
                    curve_a_data = process_iv_data(data, "A")
                except Exception as e:
                    curve_a_data = None
                    print("String A not available. Error: ", e)
                try:
                    curve_b_data = process_iv_data(data, "B")
                except Exception as e:
                    curve_b_data = None
                    print("String B not available. Error: ", e)
                return curve_a_data, curve_b_data
        else:
            print(f"Failed to get job status: {response.status_code}")
            print("Response Body:", response.text)
            return None
        time.sleep(2)


def start_ivcurve(username, password):
    """
    Initiates the process of starting an IV curve measurement by obtaining an
    authorization token using provided credentials, making a request to the IV
    curve API to begin the measurement, and handling the response to ensure the
    process starts successfully or outputting error details if it fails.

    :return: Result of the IV curve status polling if started successfully, else None.
    """
    token = get_token(username, password)
    if token:
        url = "https://fei-nu211/api/v1/ivcurve/start"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, verify=False)
        if response.status_code == 200:
            print("IV curve process started successfully.")
            return poll_ivcurve_status(token)
        else:
            print(f"Failed to start IV curve process: {response.status_code}")
            print("Response Body:", response.text)
            return None
    return "None"
