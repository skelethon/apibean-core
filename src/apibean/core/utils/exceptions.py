from typing import Optional

exceptions_by_name = dict()
exceptions_by_code = dict()


class ExceptionMeta(type):
    def __new__(cls, name, bases, dct,
            error_code_required: bool = False,
            error_code: Optional[str] = None,
            error_description: Optional[str] = None):
        new_class = super().__new__(cls, name, bases, dct)

        if new_class != Exception and issubclass(new_class, Exception):
            exceptions_by_name.update({name: new_class})

            if error_code is not None:
                new_class.error_code = error_code
            error_code = getattr(new_class, "error_code", None)

            if error_code is None:
                if error_code_required:
                    raise Exception("error_code must not be None")
            else:
                if error_code in exceptions_by_code:
                    raise Exception("error_code is duplicated")
                exceptions_by_code.update({error_code: new_class})

            if error_description is not None:
                new_class.error_description = error_description

        return new_class


def __extract_exception_info(exc: Exception, docstring_to_list:bool=True):
    if exc is None:
        raise Exception("The first argument must be an Exception class")
    if not issubclass(type(exc), ExceptionMeta):
        raise Exception(f"This class is not created by '{ExceptionMeta.__name__}'")

    mc = type(exc)
    return dict(
        error_code=getattr(exc, "error_code", None),
        error_description=getattr(exc, "error_description", None),
        name=exc.__name__,
        module=exc.__module__,
        metaclass=dict(name=mc.__name__, module=mc.__module__) if mc else None,
        doc=exc.__doc__.split("\n") if exc.__doc__ is not None and docstring_to_list else exc.__doc__,
    )


def read_exception_by_name(name: str, docstring_to_list:bool=True) -> dict:
    return __extract_exception_info(exceptions_by_name[name], docstring_to_list)


def read_exception_by_code(code: str, docstring_to_list:bool=True) -> dict:
    return __extract_exception_info(exceptions_by_code[code], docstring_to_list)


def get_exceptions_list(iterator_as_output: bool=False):
    iterator = map(lambda e: read_exception_by_name(e, True), exceptions_by_name.keys())
    return iterator if iterator_as_output else list(iterator)


def get_exceptions_dict():
    return {e: read_exception_by_name(e) for e in exceptions_by_name }


def reset_exceptions_store():
    exceptions_by_name.clear()
    exceptions_by_code.clear()
