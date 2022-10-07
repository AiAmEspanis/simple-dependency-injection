import random
import unittest
from abc import ABC, abstractmethod

from simple_dependency_injection.dependency_container import (
    DependencyContainer,
    DependencyFunctionError,
    DependencyNotRegistered,
    DependencyInjectionError,
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

    def test_register_dependency_with_variables_inside_function(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            var_test = 1
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

    def test_register_singleton_dependency(self):
        class BasicSingletonDependencyInterface(ABC):
            @abstractmethod
            def get_random_number(self) -> int:
                pass

        class BasicSingletonDependency(BasicSingletonDependencyInterface):
            def __init__(self):
                self._random = random.randint(1, 100)

            def get_random_number(self) -> int:
                return self._random

        def basic_singleton_dependency_generator() -> BasicSingletonDependencyInterface:
            return BasicSingletonDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicSingletonDependencyInterface,
            basic_singleton_dependency_generator,
            singleton=True,
        )

        output_1 = dependency_container.get_dependency(
            BasicSingletonDependencyInterface
        )
        output_2 = dependency_container.get_dependency(
            BasicSingletonDependencyInterface
        )

        self.assertEqual(output_1.get_random_number(), output_2.get_random_number())

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

    def test_get_dependency_not_registered(self):

        dependency_container = DependencyContainer()

        with self.assertRaises(DependencyNotRegistered) as ex:
            dependency_container.get_dependency(BasicDependencyInterface)
        self.assertEqual(
            "BasicDependencyInterface is not registered",
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

    def test_inject_basic_with_more_than_one_parameter(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(
            basic_dependency: BasicDependencyInterface, test_parameter: int
        ) -> str:
            return basic_dependency.get_message_data() + str(test_parameter)

        output = main(test_parameter=1)

        self.assertEqual(output, "test1")

    def test_inject_basic_with_position_arguments(self):
        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(
            basic_dependency: BasicDependencyInterface, test_parameter: int
        ) -> str:
            return basic_dependency.get_message_data() + str(test_parameter)

        with self.assertRaises(DependencyInjectionError) as ex:
            main(1)
        self.assertEqual(
            "Injected function not accept position arguments",
            str(ex.exception),
        )

    def test_inject_basic_overriding_dependency_in_parameters(self):
        class BasicDependencyNew(BasicDependencyInterface):
            def get_message_data(self) -> str:
                return "test other dependency"

        def basic_dependency_generator() -> BasicDependencyInterface:
            return BasicDependency()

        dependency_container = DependencyContainer()
        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator
        )

        @dependency_container.inject
        def main(basic_dependency: BasicDependencyInterface) -> str:
            return basic_dependency.get_message_data()

        output = main(basic_dependency=BasicDependencyNew())
        self.assertEqual(output, "test other dependency")

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

    def test_save_and_restore_dependencies(self):
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

        dependency_container.save()

        dependency_container.register_dependency(
            BasicDependencyInterface, basic_dependency_generator_v2
        )
        output = main()

        self.assertEqual(output, "test_2")

        dependency_container.restore()

        output = main()

        self.assertEqual(output, "test")
