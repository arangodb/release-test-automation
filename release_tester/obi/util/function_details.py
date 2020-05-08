def args_to_str(*args, **kwargs):
    """ create string representation of *args and **kwargs """
    rv = ""
    for arg in args:
        rv += "{0}, ".format(str(arg))
    for key, val in kwargs:
        rv += "{0} = {1}, ".format(key,str(val))
    return rv.rstrip(', ')
