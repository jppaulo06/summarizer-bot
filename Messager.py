from lib import Port, Adapter, print_debug
import telebot
from threading import Thread
from enum import Enum
from abc import abstractmethod


class MessagerAdapter(Adapter):
    @abstractmethod
    def __init__(self, key: str) -> None:
        pass

    @abstractmethod
    def run(self, message: str) -> str:
        pass


class TelegramAdapter(MessagerAdapter):
    class Context:
        class State(Enum):
            WELCOME = 0
            NOT_SUMMARIZING = 1
            SUMMARIZING = 2

        __state: State
        __chat_id: str

        def __init__(self, chat_id: str) -> None:
            self.__state = self.State.WELCOME
            self.__chat_id = chat_id

        def set_not_summarizing(self):
            self.__state = self.State.NOT_SUMMARIZING

        def set_summarizing(self):
            self.__state = self.State.SUMMARIZING

        def is_summarizing(self) -> bool:
            return self.__state == self.State.SUMMARIZING

        def chat_id(self) -> str:
            return self.__chat_id

    contexts: list[Context] = []
    bot: telebot.TeleBot

    def __init__(self, key: str) -> None:
        self.bot = telebot.TeleBot(key)

        print_debug("Telegram bot initialized")

        @self.bot.message_handler(commands=["start"])
        def start(message: telebot.types.Message):
            print_debug("Received start message")

            response = """
Olá!

*Sou um Bot de resumir e-mails do USPCodelab!*

Para iniciar o resumo de um e-mail, envie a mensagem \
```/summarize```. Caso deseje parar o resumo, envie \
```/stop```.
            """
            self.contexts.append(self.Context(message.chat.id))
            self.bot.reply_to(message, response)

        @self.bot.message_handler(commands=["summarize"])
        def summarize(message: telebot.types.Message):
            print_debug("Received summarize message")

            ctx = self.__get_context(message.chat.id)

            if ctx is None:
                self.bot.reply_to(
                    message, "Inicialize o bot com o comando /start")
                return
            if not self.__has_permission(message, ctx):
                self.bot.reply_to(
                    message, "Apenas administradores podem fazer isso")
                return

            ctx.set_summarizing()
            self.bot.reply_to(message, "Resumo de e-mails ativado")

        @self.bot.message_handler(commands=["stop"])
        def stop(message: telebot.types.Message):
            print_debug("Received stop message")

            ctx = self.__get_context(message.chat.id)

            if ctx is None:
                self.bot.reply_to(
                    message, "Inicialize o bot com o comando /start")
                return
            if not self.__has_permission(message, ctx):
                self.bot.reply_to(
                    message, "Apenas administradores podem fazer isso")
                return

            ctx.set_not_summarizing()
            self.bot.reply_to(message, "Resumo de e-mails desativado")

        Thread(target=self.bot.infinity_polling).start()

    def run(self, message: str) -> None:
        for ctx in self.contexts:
            if ctx.is_summarizing():
                self.bot.send_message(ctx.chat_id(), message)

    def __get_context(self, chat_id: str) -> Context or None:
        for ctx in self.contexts:
            if ctx.chat_id() == chat_id:
                return ctx
        return None

    def __has_permission(self, message: telebot.types.Message, ctx: Context) -> bool:
        return message.chat.type == "private" \
            or message.from_user.id in self.__get_admin_ids(ctx)

    def __get_admin_ids(self, ctx: Context) -> list[str]:
        return [admin.user.id for admin in
                self.bot.get_chat_administrators(ctx.chat_id())]


class StdoutAdapter(MessagerAdapter):
    def __init__(self, key: str) -> None:
        _ = key

    def run(self, message: str) -> None:
        print(message)


class Messager(Port):
    adapter: MessagerAdapter

    def __init__(self, adapter: str, key: str) -> None:
        self.adapter = self.__get_adapter(adapter, key)

    def run(self, message: str) -> None:
        message = "[Resumo de E-mail]\n\n" + message
        self.adapter.run(message)

    def __get_adapter(self, adapter: str, key: str) -> MessagerAdapter:
        if adapter == "stdout":
            return StdoutAdapter(key)
        elif adapter == "telegram":
            return TelegramAdapter(key)
        else:
            raise ValueError("Invalid messager adapter")
