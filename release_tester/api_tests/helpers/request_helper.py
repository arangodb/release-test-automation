""" API tests request helper """
import json
import requests

from pathlib import Path

from reporting.reporting_utils import step, attach_http_request_to_report, attach_http_response_to_report

HTTP_METHODS = {"get": requests.get, "post": requests.post, "put": requests.put, "patch": requests.patch}


@step
def execute_request_arangosh(starter_instance, request_data):
    """send an http request with JSON payload to the frontend instance using arangosh"""

    result_json_path = f"{Path(__file__).parent.parent.resolve()}/request_data/response.json"
    fe_instance = [instance for instance in starter_instance.all_instances if instance.is_frontend()][0]
    base_url = fe_instance.get_public_plain_url()
    full_url = starter_instance.get_http_protocol() + "://" + base_url + request_data["endpoint"]

    js_script = """
        const fs = require('fs');
        const request = require('@arangodb/request');
        const res = request({
            method: '%s',
            url: '%s',
    """ % (request_data["method"], full_url)
    if 'headers' in request_data:
        js_script += """
            headers: %s,
        """ % (json.dumps(request_data["headers"]))
    if 'payload' in request_data:
        js_script += """
            body: %s,
            json: true,
       """ % (json.dumps(request_data["payload"]))
    js_script += """
            auth: {bearer: '%s'}
        });
        fs.write('%s', JSON.stringify(res));
    """ % (
        str(starter_instance.get_jwt_header()),
        result_json_path
    )
    starter_instance.arangosh.run_command(("execute http request in arangosh", js_script), verbose=False)
    result = {"body": "{}"}
    with open(result_json_path, "r", encoding="utf-8") as f:
        result = json.load(f)
    return json.loads(result["body"])


@step
def execute_request_python(starter_instance, request_data):
    """send an http request with JSON payload to the frontend instance"""

    verb_method = HTTP_METHODS[request_data["method"]]
    request_headers = request_data["headers"]
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
    return response.json()
