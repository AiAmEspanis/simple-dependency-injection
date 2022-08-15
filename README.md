# simple-dependency-injection

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=AiAmEspanis_simple-dependency-injection&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=AiAmEspanis_simple-dependency-injection)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=AiAmEspanis_simple-dependency-injection&metric=coverage)](https://sonarcloud.io/summary/new_code?id=AiAmEspanis_simple-dependency-injection)

simple-dependency-injection is a library is lightweight library to apply dependency injection pattern in a simple way.

**Note:** simple-dependency-injection is in a development state, there were some checks to finish the first version

## Install

You can install it through pip

``pip install simple-dependency-injection``


## Use

To use simple-dependency-injection only have to create a dependency container and register your dependencies.

The library check types of parameters and result, its important typing that.

That is an example of dependency container configuration

```
from abc import ABC, abstractmethod
from simple_dependency_injection.dependency_container import DependencyContainer

class ConfigDependencyInterface(ABC):
    @abstractmethod
    def get_percent_benefit(self) -> float:
        pass

class ConfigDependency(ConfigDependencyInterface):
    def get_percent_benefit(self) -> float:
        return 10.0
   
def config_generator() -> ConfigDependencyInterface:
    return ConfigDependency()

class ServiceInterface(ABC):
    def __init__(self, config: ConfigDependencyInterface):
        self.config = config

    @abstractmethod
    def calculate_benefit(self, amount: float) -> float:
        pass

class Service(ServiceInterface):
    def calculate_benefit(self, amount: float) -> float:
        return amount * (self.config.get_percent_benefit() / 100)
  
def service_generator(config: ConfigDependencyInterface) -> ServiceInterface:
    return Service(config=config)

dependency_container = DependencyContainer()
dependency_container.register_dependency(
    ConfigDependencyInterface, config_generator
)
dependency_container.register_dependency(
    ServiceInterface, service_generator
)
```

Once the dependency container is created, you can use it with inject decorator.
```
@dependency_container.inject
def main(service: ServiceInterface):
    service.calculate_benefit(10)

main()
```

Other way to use the dependency container is get the dependency directly
```
dependency_container.get_dependency(ServiceInterface).calculate_benefit(10)
```

For testing is easy override dependencies
```
class ConfigToTestDependency(ConfigDependencyInterface):
    def get_percent_benefit(self) -> float:
        return 0.0

def test_config_generator() -> ConfigDependencyInterface:
    return ConfigToTestDependency()

with dependency_container.test_container() as dependency_container_test:
    dependency_container_test.override(
        ConfigDependencyInterface, test_config_generator
    )
    main()
```
