#!/usr/bin/env python3
""" convert cli options from click to structures """

# pylint: disable=too-few-public-methods
class OptionGroup:
    """wrapper class to init from kwargs"""

    @classmethod
    def from_dict(cls, **options):
        """invoke init from kwargs"""
        # these members will be added by derivative classes:
        # pylint: disable=no-member disable=fixme
        # TODO: after we upgrade to python 3.10, we should replace this with {}|{} operator
        dict1 = {key: value for key, value in options.items() if key in cls.__dataclass_fields__}
        dict2 = {
            key: value.type.from_dict(**options)
            for key, value in cls.__dataclass_fields__.items()
            if OptionGroup in value.type.mro()
        }
        for key, value in dict2.items():
            dict1[key] = value
        return cls(**(dict1))
