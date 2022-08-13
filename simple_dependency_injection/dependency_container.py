from functools import partial
from typing import Any, Type


class DependencyNotRegistered(Exception):
    pass


class DependencyFunctionError(Exception):
    pass


class DependencyContainerState:
    def __init__(self, dependencies):
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies


class DependencyContainer:
    def __init__(self):
        self._dependencies = {}

    def register_dependency(self, dependency_interface: Type, dependency_function):
        self._check_dependency_function(dependency_function=dependency_function)
        self._dependencies[dependency_interface] = self.inject(dependency_function)

    def _check_dependency_function(self, dependency_function):
        function_annotations = dependency_function.__annotations__
        parameters_annotations = {
            annotation: function_annotations[annotation]
            for annotation in function_annotations
            if annotation != "return"
        }

        parameters_not_typed = [
            parameter
            for parameter in dependency_function.__code__.co_varnames
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
        return self._dependencies[dependency_interface]()

    def exists_dependency(self, dependency_interface: Type):
        return dependency_interface in self._dependencies

    def inject(self, func):
        def function_injected(*args, **kwargs):
            function_annotations = func.__annotations__
            parameters_annotations = {
                annotation: function_annotations[annotation]
                for annotation in function_annotations
                if annotation != "return"
            }
            return_annotation = function_annotations.get("return", None)

            dependency_kwargs = {}
            for params_name in parameters_annotations:
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

    def test_container(self):
        return DependencyContainerFake(dependency_container=self)

    def save(self) -> DependencyContainerState:
        return DependencyContainerState(dependencies=self._dependencies.copy())

    def restore(self, memento: DependencyContainerState):
        self._dependencies = memento.get_dependencies()


class DependencyContainerFake:
    def __init__(self, dependency_container: DependencyContainer):
        self._dependency_container = dependency_container
        self._old_state = self._dependency_container.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.reset()

    def override(self, dependency_interface, dependency_function):
        self._dependency_container.register_dependency(
            dependency_interface=dependency_interface,
            dependency_function=dependency_function,
        )

    def reset(self):
        self._dependency_container.restore(self._old_state)
