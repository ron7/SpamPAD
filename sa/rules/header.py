"""Rules that check headers."""

import sa.regex
import sa.rules.base


class HeaderRule(sa.rules.base.BaseRule):
    """Abstract base class for all header rules."""
    def match(self, msg):
        raise NotImplementedError()

    @classmethod
    def get_rule(cls, name, data):
        kwargs = cls.get_rule_kwargs(data)
        value = data["value"]

        if "=~" in value:
            header_name, pattern = data["value"].split("=~", 1)
            header_name = header_name.strip()
            kwargs["pattern"] = sa.regex.perl2re(pattern)
            if header_name == "ALL":
                return _AllHeaderRule(name, **kwargs)
            if header_name == "ToCc":
                return _ToCcHeaderRule(name, **kwargs)
            if header_name == "MESSAGEID":
                return _MessageIDHeaderRule(name, **kwargs)

            if ":" in header_name:
                header_name, mod = header_name.rsplit(":", 1)
                kwargs["header_name"] = header_name.strip()
                if mod == "raw":
                    return _PatternRawHeaderRule(name, **kwargs)
                if mod == "addr":
                    return _AddrHeaderRule(name, **kwargs)
                if mod == "name":
                    return _NameHeaderRule(name, **kwargs)
            else:
                kwargs["header_name"] = header_name.strip()
                return _PatternHeaderRule(name, **kwargs)
        elif data["value"].startswith("exists:"):
            kwargs["header_name"] = data["value"].lstrip("exists:").strip()
            return _ExistsHeaderRule(name, **kwargs)


class _ExistsHeaderRule(HeaderRule):
    """Simple check if header exists."""
    def __init__(self, name, header_name, score=None, desc=None):
        HeaderRule.__init__(self, name, score=score, desc=desc)
        self._header_name = header_name

    def match(self, msg):
        return self._header_name in msg.raw_headers


class _PatternHeaderRule(HeaderRule):
    """Matches a header by name and a regular expression for the value. The
    headers are decoded, and the header name is NOT included.
    """
    def __init__(self, name, pattern=None, header_name=None, score=None,
                 desc=None):
        super(HeaderRule, self).__init__(name, score=score, desc=desc)
        self._header_name = header_name
        self._pattern = pattern

    def match(self, msg):
        for value in msg.get_decoded_header(self._header_name):
            if self._pattern.match(value):
                return True
        return False


class _PatternRawHeaderRule(_PatternHeaderRule):
    """Matches a header by name and a regular expression for the value. The
    headers are NOT decoded, and the header name is NOT included.
    """
    def match(self, msg):
        for value in msg.get_raw_header(self._header_name):
            if self._pattern.match(value):
                return True
        return False


class _AddrHeaderRule(_PatternHeaderRule):
    """Matches a header by name and a regular expression for the value. The
    value checked is the first address that appears in the header's value.
    """
    def match(self, msg):
        for value in msg.get_addr_header(self._header_name):
            if self._pattern.match(value):
                return True
        return False


class _NameHeaderRule(_PatternHeaderRule):
    """Matches a header by name and a regular expression for the value. The
    value checked is the first name that appears in the header's value.
    """
    def match(self, msg):
        for value in msg.get_name_header(self._header_name):
            if self._pattern.match(value):
                return True
        return False


class _MultiplePatternHeaderRule(HeaderRule):
    """Does a simple pattern check against multiple decoded headers."""
    _headers = None

    def __init__(self, name, pattern, score=None, desc=None):
        HeaderRule.__init__(self, name, score=score, desc=desc)
        self._pattern = pattern

    def match(self, msg):
        for header_name in self._headers or ():
            for value in msg.get_decoded_header(header_name):
                if self._pattern.match(value):
                    return True
        return False


class _ToCcHeaderRule(_MultiplePatternHeaderRule):
    """Matches the To and Cc headers by  a regular expression. The headers are
    decoded, and the header name is NOT included.
    """
    _headers = ("To", "Cc")


class _MessageIDHeaderRule(_MultiplePatternHeaderRule):
    """Matches various MessageID headers by  a regular expression. The headers
    are decoded, and the header name is NOT included.
    """
    _headers = ("Message-Id", "Resent-Message-Id", "X-Message-Id")


class _AllHeaderRule(HeaderRule):
    """Matches the pattern against all headers. In this case the header
    name IS included in the search, and headers are decoded.
    """
    def __init__(self, name, pattern, score=None, desc=None):
        HeaderRule.__init__(self, name, pattern, score=score, desc=desc)

    def match(self, msg):
        for header in msg.iter_decoded_headers():
            if self._pattern.match(header):
                return True
        return False
