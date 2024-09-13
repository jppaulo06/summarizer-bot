from abc import ABC, abstractmethod
from enum import Enum


class Colors:
    OK = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def print_error(message: str):
    print(f"{Colors.FAIL}[Error] {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.OK}[INFO] {message}{Colors.ENDC}")


class Port(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass


class Adapter(Port):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass
