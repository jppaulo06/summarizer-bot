from dotenv import load_dotenv
from Reader import Reader
from Summarizer import Summarizer
from Messager import Messager
from Core import Core
import os


def setup():
    load_dotenv()


if __name__ == "__main__":
    setup()

    reader = Reader(os.getenv("READER"),
                    os.getenv("READER_USER"),
                    os.getenv("READER_KEY"),
                    os.getenv("READER_SENDERS").split(","))

    summarizer = Summarizer(os.getenv("SUMMARIZER"),
                            os.getenv("SUMMARIZER_KEY"))

    messager = Messager()
    core = Core(reader, summarizer, messager)
    core.run()
