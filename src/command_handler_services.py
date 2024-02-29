from telegram.ext import BaseHandler


class CommandHandlerServices:
    def __init__(self, name: str, handler: BaseHandler, desc: str) -> None:
        self.handler = handler
        self.name = name
        self.description = desc
