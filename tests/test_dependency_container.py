import unittest
from abc import ABC, abstractmethod

from simple_dependency_injection.dependency_container import DependencyContainer


class BasicDependencyInterface(ABC):

    @abstractmethod
    def get_data(self) -> str:
        pass


class BasicDependency(BasicDependencyInterface):

    def get_data(self) -> str:
        return "test"


class BasicDependencyVersion2(BasicDependencyInterface):

    def get_data(self) -> str:
        return "test_2"


def basic_dependency_generator() -> BasicDependencyInterface:
    return BasicDependency()


def basic_dependency_version_2_generator() -> BasicDependencyInterface:
    return BasicDependencyVersion2()


class ComposeDependencyInterface(ABC):

    @abstractmethod
    def get_data(self) -> str:
        pass


class ComposeBasicDependency(ComposeDependencyInterface):

    def __init__(self, message_to_return: str):
        self._message_to_return = message_to_return

    def get_data(self) -> str:
        return self._message_to_return


def compose_dependency_generator(basic_dependency: BasicDependencyInterface) -> ComposeDependencyInterface:
    return ComposeBasicDependency(message_to_return=basic_dependency.get_data())


class TestDependencyContainer(unittest.TestCase):

    def test_dependency_container_inject_basic(self):
        dependency_container = DependencyContainer()
        dependency_container.register_dependency(BasicDependencyInterface, basic_dependency_generator)

        @dependency_container.inject
        def main(basic_dependency: BasicDependencyInterface) -> str:
            return basic_dependency.get_data()

        output = main()

        self.assertEqual(output, "test")

    def test_dependency_container_inject_compose_dependency(self):
        dependency_container = DependencyContainer()
        dependency_container.register_dependency(BasicDependencyInterface, basic_dependency_generator)
        dependency_container.register_dependency(ComposeDependencyInterface, compose_dependency_generator)

        @dependency_container.inject
        def main(compose_dependency: ComposeDependencyInterface) -> str:
            return compose_dependency.get_data()

        output = main()

        self.assertEqual(output, "test")

    def test_dependency_container_override_dependency(self):
        dependency_container = DependencyContainer()
        dependency_container.register_dependency(BasicDependencyInterface, basic_dependency_generator)
        dependency_container.register_dependency(ComposeDependencyInterface, compose_dependency_generator)

        @dependency_container.inject
        def main(compose_dependency: ComposeDependencyInterface) -> str:
            return compose_dependency.get_data()

        with dependency_container.test_container() as dependency_container_test:
            dependency_container_test.override(BasicDependencyInterface, basic_dependency_version_2_generator)
            output = main()

        self.assertEqual(output, "test_2")

        output = main()

        self.assertEqual(output, "test")
