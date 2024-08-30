from rest_framework.parsers import BaseParser

class JSONSizeLimitParser(BaseParser):
    media_type = 'application/json'
    def __init__(self, *args):
        print("\n\n\nCUSTOM PARSER INITIALIZED!!!\n\n\n")
        super().__init__(*args)

    def parse(self, stream, media_type=None, parser_context=None):
        print("\n\n\n\nCUSTOM PARSING GOING ON HERE!!!!!!!!!\n\n\n\n")
        raise PermissionError
        return super().parse(stream, media_type, parser_context)