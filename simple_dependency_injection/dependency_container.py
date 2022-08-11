from functools import partial


class DependencyContainerMemento:

    def __init__(self, dependencies):
        self._dependencies = dependencies

    def get_dependencies(self):
        return self._dependencies


class DependencyContainer:

    def __init__(self):
        self._dependencies = {}

    def register_dependency(self, dependency_interface, dependency_function):
        self._dependencies[dependency_interface] = self.inject(dependency_function)

    def inject(self, func):
        def function_injected(*args, **kwargs):
            dependency_kwargs = {}
            for params_name in func.__annotations__:
                if params_name != "return":
                    dependency_kwargs[params_name] = self._dependencies[func.__annotations__[params_name]]()
            new_func = partial(func, **dependency_kwargs)
            return new_func(*args, **kwargs)

        return function_injected

    def test_container(self):
        return DependencyContainerFake(dependency_container=self)

    def save(self) -> DependencyContainerMemento:
        return DependencyContainerMemento(dependencies=self._dependencies.copy())

    def restore(self, memento: DependencyContainerMemento):
        self._dependencies = memento.get_dependencies()


class DependencyContainerFake:

    def __init__(self, dependency_container: DependencyContainer):
        self._dependency_container = dependency_container
        self._old_state = self._dependency_container.save()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._dependency_container.restore(self._old_state)

    def override(self, dependency_interface, dependency_function):
        self._dependency_container.register_dependency(dependency_interface=dependency_interface, dependency_function=dependency_function)
