from lib import print_error, Port, Adapter
import imaplib
import email
from functools import reduce
from itertools import chain
import time
from abc import abstractmethod


class ReaderAdapter(Adapter):
    @abstractmethod
    def __init__(self, user: str, key: str, senders: list[str]) -> None:
        pass

    @abstractmethod
    def run(self) -> (str, str, str):
        pass


class GmailAdapter(ReaderAdapter):
    imap_url: str = "imap.gmail.com"
    polling_interval: int = 1
    user: str
    key: str
    senders: list[str]
    max_msg_id: int

    # PUBLIC METHODS

    def __init__(self, user: str, key: str, senders: list[str]) -> None:
        self.user = user
        self.key = key
        self.senders = senders
        self.max_msg_id = self.__get_max_msg_id()

    def run(self) -> str:
        while True:
            print("Waiting for new message...")

            mail = self.__setup()
            new_msg_ids = self.__get_new_msg_ids(self.max_msg_id, mail)

            for msg_id in new_msg_ids:
                if msg_id <= self.max_msg_id:
                    continue

                subject, body, origin = self.__get_content_from_msg_id(
                    msg_id, mail)

                self.max_msg_id = msg_id
                mail.logout()

                return subject, body, origin

            mail.logout()
            time.sleep(self.polling_interval)

    # PRIVATE METHODS

    def __get_max_msg_id(self) -> int:
        mail = self.__setup()

        _, data = mail.search(None, 'ALL')
        msg_ids = self.__get_ids_from_data(data)

        if len(msg_ids) == 0:
            max_msg_id = 0
        else:
            max_msg_id = max(msg_ids)

        mail.logout()

        return max_msg_id

    def __get_new_msg_ids(self, max_msg_id: int, mail: imaplib.IMAP4_SSL) -> list:
        _, data = mail.search(None, self.__search_string(
            max_msg_id, {"OR FROM": sender for sender in self.senders}))
        msg_ids = self.__get_ids_from_data(data)
        return msg_ids

    def __get_content_from_msg_id(self, msg_id: int, mail: imaplib.IMAP4_SSL) -> (str, str, str):
        _, data = mail.fetch(str(msg_id), "(RFC822)")

        body = ""
        subject = ""
        origin = ""

        for data_part in data:
            if isinstance(data_part, tuple):
                msg = email.message_from_bytes(data_part[1])
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body += payload.decode(charset)

                for subject_encoded, subject_charset in email.header.decode_header(msg["subject"]):
                    if subject_charset is not None:
                        subject += subject_encoded.decode(subject_charset)
                    elif isinstance(subject_encoded, bytes):
                        subject += subject_encoded.decode("utf-8")
                    else:
                        subject += subject_encoded

                for origin_encoded, origin_charset in email.header.decode_header(msg["from"]):
                    if origin_charset is not None:
                        origin += origin_encoded.decode(origin_charset)
                    elif isinstance(origin_encoded, bytes):
                        origin += origin_encoded.decode("utf-8")
                    else:
                        origin += origin_encoded

        return (subject, body, origin)

    def __setup(self) -> imaplib.IMAP4_SSL:
        mail = imaplib.IMAP4_SSL(self.imap_url)
        mail.login(self.user, self.key)
        mail.select('inbox')
        return mail

    def __get_ids_from_data(self, data: list) -> list:
        return reduce(lambda acc, block: acc +
                      [int(msg_id) for msg_id in block.split()], data, [])

    def __search_string(self, uid_max, criteria):
        c = list(map(lambda t: (t[0], "\"" + str(t[1]) + "\""),
                 criteria.items())) + [("UID", "%d:*" % (uid_max + 1))]
        return "(%s)" % " ".join(chain(*c))


class StdinAdapter(ReaderAdapter):
    user: str
    key: str
    senders: list[str]

    def __init__(self, user: str, key: str, senders: list[str]) -> None:
        self.user = user
        self.key = key
        self.senders = senders

    def run(self) -> (str, str, str):
        origin = input("Enter your origin: ")
        while origin not in self.senders:
            print("Ignoring message since it is not from a valid sender")
            origin = input("Enter your origin: ")

        subject = input("Enter your subject: ")
        body = input("Enter your body: ")

        if origin == self.user:
            key = input(f"Enter {self.user} key: ")
            while key != self.key:
                print("Wrong key!")
                key = input("Enter your key: ")

        return subject, body, origin


class Reader(Port):
    adapter: ReaderAdapter
    user: str
    key: str

    # PUBLIC METHODS

    def __init__(self, adapter: str, user: str, key: str, senders: list[str]) -> None:
        self.adapter = self.__get_adapter(adapter, user, key, senders)
        self.user = user
        self.key = key

    def run(self) -> str:
        subject, body, origin = self.adapter.run()
        message = f"Subject: {subject}\n\nBody:\n{body}\n\nOrigin: {origin}"
        return message

    # PRIVATE METHODS

    def __get_adapter(self, adapter: str, user: str, key: str, senders: list[str]) -> ReaderAdapter:
        if adapter == "gmail":
            return GmailAdapter(user, key, senders)
        elif adapter == "stdin":
            return StdinAdapter(user, key, senders)
        else:
            print_error("Reader Adapter not implemented")
            raise NotImplementedError
