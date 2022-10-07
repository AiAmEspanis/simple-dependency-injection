from functools import partial
from typing import Any, Type


class DependencyNotRegistered(Exception):
    pass


class DependencyFunctionError(Exception):
    pass


class DependencyInjectionError(Exception):
    pass


class DependencyContainer:
    def __init__(self):
        self._dependencies = {}
        self._saved_dependencies = {}

    def register_dependency(
        self, dependency_interface: Type, dependency_function, singleton: bool = False
    ):
        self._check_dependency_function(dependency_function=dependency_function)
        self._dependencies[dependency_interface] = {
            "singleton": singleton,
            "generator_function": self.inject(dependency_function),
        }

    def _check_dependency_function(self, dependency_function):
        function_annotations = dependency_function.__annotations__
        parameters_annotations = {
            annotation: function_annotations[annotation]
            for annotation in function_annotations
            if annotation != "return"
        }

        parameters_not_typed = [
            parameter
            for parameter in dependency_function.__code__.co_varnames[
                : dependency_function.__code__.co_argcount
            ]
            if parameter not in parameters_annotations
        ]
        if len(parameters_not_typed) > 0:
            raise DependencyFunctionError(
                f"{','.join(parameters_not_typed)} parameters are not typed"
            )

        dependencies_not_registered = [
            annotation
            for annotation in parameters_annotations
            if not self.exists_dependency(parameters_annotations[annotation])
        ]
        if len(dependencies_not_registered) > 0:
            raise DependencyFunctionError(
                f"{','.join(dependencies_not_registered)} parameters dependencies are not registered"
            )

        if "return" not in function_annotations:
            raise DependencyFunctionError("Result returned not typed")

    def get_dependency(self, dependency_interface) -> Any:
        if not self.exists_dependency(dependency_interface=dependency_interface):
            raise DependencyNotRegistered(
                f"{dependency_interface.__name__} is not registered"
            )
        dependency_config = self._dependencies[dependency_interface]
        if dependency_config["singleton"]:
            if "singleton_instance" not in dependency_config:
                dependency_config["singleton_instance"] = dependency_config[
                    "generator_function"
                ]()
            return dependency_config["singleton_instance"]
        return self._dependencies[dependency_interface]["generator_function"]()

    def exists_dependency(self, dependency_interface: Type):
        return dependency_interface in self._dependencies

    def inject(self, func):
        def function_injected(*args, **kwargs):
            if len(args) > 0:
                raise DependencyInjectionError(
                    "Injected function not accept position arguments"
                )
            function_annotations = func.__annotations__
            parameters_annotations = {
                annotation: function_annotations[annotation]
                for annotation in function_annotations
                if annotation != "return"
            }
            return_annotation = function_annotations.get("return", None)

            dependency_kwargs = {}
            for params_name in parameters_annotations:
                if params_name not in kwargs:
                    dependency_kwargs[params_name] = self.get_dependency(
                        function_annotations[params_name]
                    )
            new_func = partial(func, **dependency_kwargs)

            result = new_func(*args, **kwargs)

            if return_annotation and not isinstance(result, return_annotation):
                raise DependencyFunctionError(
                    f"Result of function is not instance of {return_annotation.__name__}"
                )

            return result

        return function_injected

    def save(self):
        self._saved_dependencies = self._dependencies.copy()

    def restore(self):
        if self._saved_dependencies:
            self._dependencies = self._saved_dependencies
