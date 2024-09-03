from abc import ABC, abstractmethod


def print_error(message):
    print(f"[Error] {message}")


class Port(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass


class Adapter(Port):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass
