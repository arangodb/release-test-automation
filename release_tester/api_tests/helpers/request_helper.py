""" API tests request helper """
import requests

from reporting.reporting_utils import step, attach_http_request_to_report, attach_http_response_to_report

HTTP_METHODS = {"get": requests.get, "post": requests.post, "put": requests.put, "delete": requests.delete}
FIRST_PARAM = "$1"


@step
def send_request(starter_instance, request_data):
    """send an http request with JSON payload to the frontend instance"""

    verb_method = HTTP_METHODS[request_data["method"]]
    request_headers = request_data["headers"] if "headers" in request_data else {}
    request_headers["Authorization"] = "Bearer " + str(starter_instance.get_jwt_header())
    fe_instance = [instance for instance in starter_instance.all_instances if instance.is_frontend()][0]
    base_url = fe_instance.get_public_plain_url()
    full_url = starter_instance.get_http_protocol() + "://" + base_url + request_data["endpoint"]
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


def update_request_data(request_data, parameter):
    """update the request data with parameter value"""
    if "payload" in request_data:
        for prop in request_data["payload"].keys():
            if isinstance(request_data["payload"][prop], str):
                request_data["payload"][prop] = request_data["payload"][prop].replace(FIRST_PARAM, parameter)
    if "endpoint" in request_data:
        request_data["endpoint"] = request_data["endpoint"].replace(FIRST_PARAM, parameter)
    return request_data
