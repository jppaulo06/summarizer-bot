import os
from lib import Port


class Messager(Port):
    def run(self, message: str) -> None:
        if os.getenv("DEBUG") == "True":
            print(message)
            return

        adapter = os.getenv("MESSAGE")

        if adapter == "telegram":
            # TODO: Implement Telegram Adapter
            raise NotImplementedError
