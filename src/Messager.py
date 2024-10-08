from lib import Port, Adapter, print_info
import telebot
import discord
from discord.ext import commands
from threading import Thread
from enum import Enum
from abc import abstractmethod
import asyncio


class MessagerAdapter(Adapter):
    @abstractmethod
    def __init__(self, key: str) -> None:
        pass

    @abstractmethod
    def run(self, message: str) -> str:
        pass


class MessagerChatContext:
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


class TelegramAdapter(MessagerAdapter):
    contexts: list[MessagerChatContext] = []
    bot: telebot.TeleBot
    welcome_message = """
Olá!

*Sou um Bot de resumir e-mails do USPCodelab!*

Para iniciar o resumo de um e-mail, envie a mensagem \
```/summarize```.

Caso deseje parar o resumo, envie ```/stop```.
"""

    def __init__(self, key: str) -> None:
        self.bot = telebot.TeleBot(key)

        print_info("Telegram bot initialized")

        @self.bot.message_handler(commands=["start"])
        def start(message: telebot.types.Message):
            print_info("Received start message")
            self.contexts.append(MessagerChatContext(message.chat.id))
            self.bot.reply_to(message, self.welcome_message)

        @self.bot.message_handler(commands=["summarize"])
        def summarize(message: telebot.types.Message):
            print_info("Received summarize message")

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
            print_info("Received stop message")

            ctx = self.__get_context(message.chat.id)

            if ctx is None:
                self.bot.reply_to(
                    message, "Inicialize o bot com o comando /start!")
                return

            if not self.__has_permission(message, ctx):
                self.bot.reply_to(
                    message, "Apenas administradores podem fazer isso :/")
                return

            ctx.set_not_summarizing()
            self.bot.reply_to(message, "Resumo de e-mails desativado!")

        Thread(target=self.bot.infinity_polling).start()

    def run(self, message: str) -> None:
        print_info("Sending telegram message")
        for ctx in self.contexts:
            if ctx.is_summarizing():
                self.bot.send_message(ctx.chat_id(), message)

    def __get_context(self, chat_id: str) -> MessagerChatContext or None:
        for ctx in self.contexts:
            if ctx.chat_id() == chat_id:
                return ctx
        return None

    def __has_permission(self, message: telebot.types.Message, ctx: MessagerChatContext) -> bool:
        return message.chat.type == "private" \
            or message.from_user.id in self.__get_admin_ids(ctx)

    def __get_admin_ids(self, ctx: MessagerChatContext) -> list[str]:
        return [admin.user.id for admin in
                self.bot.get_chat_administrators(ctx.chat_id())]


class DiscordAdapter(MessagerAdapter):
    contexts: list[MessagerChatContext] = []
    welcome_message = """
Olá!

**Sou um Bot de resumir e-mails do USPCodelab!**

Para iniciar o resumo de um e-mail, envie a mensagem \
`!summarize`.

Caso deseje parar o resumo, envie `!stop`.
"""

    def __init__(self, key: str) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = discord.Client(intents=intents)

        @self.bot.event
        async def on_ready():
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        await channel.send(self.welcome_message)
                        self.contexts.append(MessagerChatContext(channel.id))
                        break
            print_info("Discord bot initialized")

        @self.bot.event
        async def on_guild_join(guild):
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(self.welcome_message)
                    self.contexts.append(MessagerChatContext(channel.id))
                    break

        @self.bot.event
        @commands.has_permissions(administrator=True)
        async def on_message(message):
            if message.author == self.bot.user:
                return

            channel_id = message.channel.id
            ctx = self.__get_context(channel_id)

            if ctx is None:
                return

            print_info(f"Received message: {message.content}")

            if message.content.startswith("!start"):
                ctx.set_summarizing()
                await message.channel.send(self.welcome_message)

            if message.content.startswith("!summarize"):
                ctx.set_summarizing()
                await message.channel.send("Resumo de e-mails ativado!")

            if message.content.startswith("!stop"):
                ctx.set_not_summarizing()
                await message.channel.send("Resumo de e-mails desativado!")

        Thread(target=self.bot.run, args=(key,)).start()

    def run(self, message: str) -> None:
        print_info(f"Sending discord message")
        for ctx in self.contexts:
            if ctx.is_summarizing():
                asyncio.run_coroutine_threadsafe(
                    self.bot.get_channel(ctx.chat_id()).send(message),
                    self.bot.loop
                )

    def __get_context(self, channel_id: str) -> MessagerChatContext or None:
        for ctx in self.contexts:
            if ctx.chat_id() == channel_id:
                return ctx
        return None


class StdoutAdapter(MessagerAdapter):
    def __init__(self, key: str) -> None:
        _ = key

    def run(self, message: str) -> None:
        print_info("Sending stdout message")
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
        elif adapter == "discord":
            return DiscordAdapter(key)
        else:
            raise ValueError("Invalid messager adapter")
