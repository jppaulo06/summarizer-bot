from lib import print_error, Port, Adapter
from abc import abstractmethod
import maritalk


class SummarizerAdapter(Adapter):
    @abstractmethod
    def __init__(self, key: str) -> None:
        pass

    @abstractmethod
    def run(self, message: str) -> str:
        pass


class MaritacaAdapter(SummarizerAdapter):
    model: maritalk.MariTalk
    model_type: str = "sabia-3"

    def __init__(self, key: str) -> None:
        self.model = maritalk.MariTalk(key=key, model=self.model_type)

    def run(self, message: str) -> str:
        prompt = """
Resuma o e-mail a seguir. Não passe de 10 linhas.

Mencione inicialmente o assunto original do e-mail em negrito, por exemplo

"*[assunto do e-mail original]*

[Resumo do E-mail]
"

Responda sempre em português brasileiro.

E-mail a ser resumido:

\n{message}
        """.format(message=message)
        response = self.model.generate(
            prompt,
            max_tokens=200)

        summary = response["answer"]
        return summary


class SimpleAdapter(SummarizerAdapter):
    def __init__(self, key: str) -> None:
        _ = key

    def run(self, message: str) -> str:
        return message[:100]


class Summarizer(Port):
    adapter: SummarizerAdapter
    key: str

    # PUBLIC METHODS

    def __init__(self, adapter: str, key: str) -> None:
        self.adapter = self.__get_adapter(adapter, key)
        self.key = key

    def run(self, message: str) -> str:
        summary = self.adapter.run(message)
        return summary

    # PRIVATE METHODS

    def __get_adapter(self, adapter: str, key: str) -> SummarizerAdapter:
        if adapter == "maritaca":
            return MaritacaAdapter(key)
        elif adapter == "simple":
            return SimpleAdapter(key)
        else:
            print_error("Summarizer Adapter not implemented")
            raise NotImplementedError
