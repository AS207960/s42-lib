import dataclasses
import re

CODE_RE = re.compile(
    r"^(?:(?P<issuer>[A-Z]))?(?P<code>[0-9]{2})\.(?P<subtype>[0-9]{2})(?:\.(?P<instance>[0-9]{2})\.(?P<part>[0-9]{2}))?$")


@dataclasses.dataclass(frozen=True)
class Code:
    code: int
    subtype: int
    instance: int = 0
    part: int = 0
    issuer: str = 'U'

    @property
    def base(self):
        return type(self).fromstring("{0}{1:02d}.{2:02d}".format(self.issuer, self.code, self.subtype))

    @classmethod
    def fromstring(cls, code):
        try:
            kwargs = CODE_RE.match(code).groupdict()
        except AttributeError:
            raise ValueError("Invalid code: " + code)
        return cls(
            issuer=kwargs["issuer"],
            code=int(kwargs["code"]),
            subtype=int(kwargs["subtype"]),
            instance=int(kwargs["instance"]) if kwargs["instance"] else 0,
            part=int(kwargs["part"]) if kwargs["part"] else 0,
        )

    def is_base(self):
        return self.instance is None

    def __str__(self):
        element = "{0}{1:02d}.{2:02d}".format(
            self.issuer, self.code, self.subtype)
        if self.instance is not None:
            assert self.part is not None
            element += ".{0:02d}.{1:02d}".format(self.instance, self.part)
        return element

    def __repr__(self):
        return "<Code: {0}>".format(str(self))


@dataclasses.dataclass(frozen=True)
class LineIdentifier:
    numeric: int
    symbolic: str

    @classmethod
    def from_xml(cls, element):
        assert element.tag == 'lineName'
        return cls(int(element.get('lineNumber')), element.text)


class AddressDTO:
    @classmethod
    def fromdict(cls, dto):
        return cls(dto)

    def __init__(self, elements):
        self._elements = {}
        for code, value in elements.items():
            code = Code.fromstring(code)
            self._elements[code] = value

    def get(self, code):
        if not isinstance(code, Code):
            code = Code.fromstring(code)
        val = self._elements.get(code)\
            or self._elements.get(code.base)

        if not val:
            return ''
        else:
            return val

    def set(self, code, value):
        if isinstance(code, str):
            code = Code.fromstring(code)
        self._elements[code] = value

    def is_populated(self, code):
        if isinstance(code, str):
            code = Code.fromstring(code)

        val = self._elements.get(code) \
              or self._elements.get(code.base)

        if not val:
            return False
        else:
            return bool(val)
