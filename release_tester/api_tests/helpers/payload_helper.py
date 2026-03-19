""" API tests payload helper """


def has_elem_with_prop_value(elem_list, prop, val):
    """checks if element with property value exists"""
    return len([elem for elem in elem_list if elem[prop] == val]) > 0


def find_elem_by_prop_value(elem_list, prop, val):
    """find element by property value"""
    return [elem for elem in elem_list if elem[prop] == val][0]


def get_elem_values_by_prop(elem_list, prop):
    """get elem values for property"""
    return [elem[prop] for elem in elem_list if prop in elem]
