""" API tests response helper """

FIRST_PARAM = "$1"


def update_request_payload(request_payload, parameter, prop="query"):
    """update the request payload"""
    if prop in request_payload:
        request_payload[prop] = request_payload[prop].replace(FIRST_PARAM, parameter)
    return request_payload


def has_elem_with_prop_value(elem_list, prop, val):
    """checks if element with property value exists"""
    return len([elem for elem in elem_list if elem[prop] == val]) > 0


def find_elem_by_prop_value(elem_list, prop, val):
    """find element by property value"""
    return [elem for elem in elem_list if elem[prop] == val][0]


def get_elem_values_by_prop(elem_list, prop):
    """get elem values for property"""
    return [elem[prop] for elem in elem_list if prop in elem]
