import unittest
from abc import ABC, abstractmethod

from simple_dependency_injection.dependency_container import (
    DependencyContainer,
    DependencyFunctionError,
)


class BasicDependencyInterface(ABC):
    @abstractmethod
    def get_message_data(self) -> str:
        pass


class BasicDependency(BasicDependencyInterface):
    def get_message_data(self) -> str:
        return "test"


class ComposedDependencyInterface(ABC):
    def __init__(self, message_to_return: str):
        self._message_to_return = message_to_return

    @abstractmethod
    def get_message(self) -> str:
        pass


class ComposedDependency(ComposedDependencyInterface):
    def get_message(self) -> str:
        return self._message_to_return


class TestDependencyContainer(unittest.TestCase):
    def test_register_dependency(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        output = dependency_container.get_dependency(BasicDependencyInterface)

        self.assertEqual(output.__class__, BasicDependency)

    def test_register_composed_dependency(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        def composed_dependency_generator(
            basic_dependency: BasicDependencyInterface,
        ) -> ComposedDependencyInterface:
            return ComposedDependency(
                message_to_return=basic_dependency.get_message_data()
            )

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )
        dependency_container.register_dependency(
            ComposedDependencyInterface, composed_dependency_generator
        )

        output = dependency_container.get_dependency(ComposedDependencyInterface)

        self.assertEqual(output.__class__, ComposedDependency)
        self.assertEqual(output.get_message(), "test")

    def test_register_dependency_with_parameters_not_typed(self):
        def test_dependency_generator(
            one_dependency, other_dependency
        ) -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()

        with self.assertRaises(DependencyFunctionError) as ex:
            dependency_container.register_dependency(
                BasicDependencyInterface, test_dependency_generator
            )
        self.assertEqual(
            "one_dependency,other_dependency parameters are not typed",
            str(ex.exception),
        )

    def test_register_dependency_with_parameters_not_registered(self):
        def test_dependency_generator(
            basic_dependency: BasicDependencyInterface,
        ) -> ComposedDependencyInterface:
            return ComposedDependency(
                message_to_return=basic_dependency.get_message_data()
            )

        dependency_container = DependencyContainer()

        with self.assertRaises(DependencyFunctionError) as ex:
            dependency_container.register_dependency(
                BasicDependencyInterface, test_dependency_generator
            )
        self.assertEqual(
            "basic_dependency parameters dependencies are not registered",
            str(ex.exception),
        )

    def test_register_dependency_with_result_not_typed(self):
        def test_dependency_generator():
            return BasicDependency()

        dependency_container = DependencyContainer()

        with self.assertRaises(DependencyFunctionError) as ex:
            dependency_container.register_dependency(
                BasicDependencyInterface, test_dependency_generator
            )
        self.assertEqual(
            "Result returned not typed",
            str(ex.exception),
        )

    def test_inject_basic(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(basic_dependency: BasicDependencyInterface) -> str:
            return basic_dependency.get_message_data()

        output = main()

        self.assertEqual(output, "test")

    def test_inject_compose_dependency(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        def composed_dependency_generator(
            basic_dependency: BasicDependencyInterface,
        ) -> ComposedDependencyInterface:
            return ComposedDependency(
                message_to_return=basic_dependency.get_message_data()
            )

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )
        dependency_container.register_dependency(
            ComposedDependencyInterface, composed_dependency_generator
        )

        @dependency_container.inject
        def main(compose_dependency: ComposedDependencyInterface) -> str:
            return compose_dependency.get_message()

        output = main()

        self.assertEqual(output, "test")

    def test_inject_with_distinct_result_type(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(basic_dependency: BasicDependencyInterface) -> float:
            return basic_dependency.get_message_data()

        with self.assertRaises(DependencyFunctionError) as ex:
            main()
        self.assertEqual(
            "Result of function is not instance of float",
            str(ex.exception),
        )

    def test_inject_without_result_returned(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(basic_dependency: BasicDependencyInterface):
            message_data = basic_dependency.get_message_data()

    def test_override_dependency(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        class BasicV2Dependency(BasicDependencyInterface):
            def get_message_data(self) -> str:
                return "test_2"

        def basic_dependency_generator_v2() -> BasicDependencyInterface:
            return BasicV2Dependency()

        def composed_dependency_generator(
            basic_dependency: BasicDependencyInterface,
        ) -> ComposedDependencyInterface:
            return ComposedDependency(
                message_to_return=basic_dependency.get_message_data()
            )

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )
        dependency_container.register_dependency(
            ComposedDependencyInterface, composed_dependency_generator
        )

        @dependency_container.inject
        def main(composed_dependency: ComposedDependencyInterface) -> str:
            return composed_dependency.get_message()

        with dependency_container.test_container() as dependency_container_test:
            dependency_container_test.override(
                BasicDependencyInterface, basic_dependency_generator_v2
            )
            output = main()

        self.assertEqual(output, "test_2")

        output = main()

        self.assertEqual(output, "test")
