class Core:
    def __init__(self, reader, summarizer, messager):
        self.reader = reader
        self.summarizer = summarizer
        self.messager = messager

    def run(self) -> None:
        while True:
            message = self.reader.run()
            summary = self.summarizer.run(message)
            self.messager.run(summary)
