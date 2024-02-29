class PakYusException(Exception):
    def __init__(self, message="", courier_name=None):
        super().__init__(message)
        self.courier_name = courier_name
