""" Operator integration tests request helper """
import json

import requests
import copy

from reporting.reporting_utils import step, attach_http_request_to_report, attach_http_response_to_report

HTTP_METHODS = {"get": requests.get, "post": requests.post, "put": requests.put, "delete": requests.delete}
PAYLOAD_PARAM_1 = "$1"
PAYLOAD_PARAM_2 = "$2"
PAYLOAD_PARAM_3 = "$3"
ENDPOINT_PARAM_1 = "#1"
ENDPOINT_PARAM_2 = "#2"
HEADER_PARAM = "!"


@step
def execute_request(request_data, base_url):
    """execute an http request"""

    verb_method = HTTP_METHODS[request_data["method"]]
    request_headers = request_data["headers"] if "headers" in request_data else {}
    full_url = base_url + request_data["endpoint"]
    attach_http_request_to_report(verb_method.__name__, full_url, request_headers, request_data["payload"])
    response = verb_method(
        full_url,
        json=request_data["payload"],
        headers=request_headers,
        allow_redirects=False,
        verify=False,
    )
    attach_http_response_to_report(response)
    try:
        json_payload = response.json()
    except requests.exceptions.JSONDecodeError:
        json_payload = {}
    return {"code": response.status_code, "json": json_payload}


def update_request_data(
    request_data,
    payload_param_1="",
    payload_param_2="",
    payload_param_3="",
    endpoint_param_1="",
    endpoint_param_2="",
    auth_token="",
):
    """update the request data with parameters values"""
    request_data_str = json.dumps(request_data)
    request_data_str = (
        request_data_str.replace(PAYLOAD_PARAM_1, payload_param_1)
        .replace(PAYLOAD_PARAM_2, payload_param_2)
        .replace(PAYLOAD_PARAM_3, payload_param_3)
        .replace(ENDPOINT_PARAM_1, endpoint_param_1)
        .replace(ENDPOINT_PARAM_2, endpoint_param_2)
        .replace(HEADER_PARAM, auth_token)
    )
    return json.loads(request_data_str)


def clone_request_data(request_data):
    """clone the request data"""
    return copy.deepcopy(request_data)
