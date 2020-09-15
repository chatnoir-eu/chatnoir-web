from rest_framework.negotiation import DefaultContentNegotiation


class FallbackContentNegotiation(DefaultContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select first parser in the list of content negotiation fails instead of erroring out.
        """
        parser = super().select_parser(request, parsers)
        if not parser:
            parser = parsers[0]

        return parser
