import inspect
    
def assert_function_signature(function,**kwargs):
    if "return_type" in kwargs:
        return_type = kwargs["return_type"]
    parameters = []
    if "parameters" in kwargs:
        parameters = kwargs["parameters"]

    if not callable(function):
        raise ValueError("Not a function")
        return
    
    sig = inspect.signature(func)

    if sig.return_annotation == inspect.Signature.empty:
        raise ValueError("Empty function return signature")
        return
    
    if sig.return_annotation != return_type:
        raise ValueError(f"Function return signature is not {return_type}")
        return
    
    if len(sig.parameters) != len(parameters):
        raise ValueError(f"Function has {len(sig.parameters)}, expected {len(parameters)} parameters")
        return
    
    index = 0
    for parameter_name in sig.parameters:
        if sig.parameters[parameter_name].annotation != parameters[index]:
            raise ValueError(f"Function parameter {index} has annotation {sig.parameters[parameter_name].annotation}, expected {parameters[index]}")
            return
        index += 1

def foo() -> int:
    return 1

def bar() -> None:
    return 1

def baz(a: int) -> int:
    print(a)
    return a

foobar = 1

funcs = (foo,bar,baz,foobar)

for func in funcs:
    print(f"Checking {func}")
    assert_function_signature(func,return_type=int,parameters=[int])