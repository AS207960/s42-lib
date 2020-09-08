import re
import collections
import xml.etree.ElementTree
from . import trigger, lines, data, rendition, exceptions


class Template:
    __procedures = collections.defaultdict(dict)

    @classmethod
    def from_file_path(cls, src):
        with open(src, 'rb') as f:
            doc = f.read()
        return cls(doc)

    def __init__(self, doc):
        self.__preconditions = []
        self.__selectors = []
        self.__lines = collections.OrderedDict()

        root = xml.etree.ElementTree.fromstring(doc)
        self.delimiter = root.findall('./contentDefinition/defaultDelimiter')[0].text.strip("'")
        self.separator = root.findall('./contentDefinition/defaultSeparator')[0].text.strip("'")
        self.sequencer = root.findall('./contentDefinition/defaultSequencer')[0].text.strip("'")
        self.collector = root.findall('./contentDefinition/defaultCollector')[0].text.strip("'")
        self.country = root.findall('./contentDefinition/templateIdentifier/countryCode')[0].text

        for el in root.findall('./contentDefinition/triggerConditions/preCondition'):
            self.__preconditions.append(trigger.Precondition.from_xml(self, el))

        for el in root.findall('./contentDefinition/triggerConditions/lineSelect'):
            self.__selectors.append(trigger.LineSelector.from_xml(self, el))

        for el in root.findall('./contentDefinition/lineData'):
            line = lines.Line.from_xml(el)
            self.__lines[line.identifier] = line

    def _get_line(self, identifier):
        return self.__lines[identifier]

    def get_selected_lines(self, dto):
        lines = []
        for selector in self.__selectors:
            candidates = selector.get_lines(dto)
            if not candidates:
                continue
            lines.extend([self._get_line(x) for x in candidates])
        return lines

    def render(self, dto, abstract=False, fail_on_missing=True):
        if isinstance(dto, dict):
            dto = data.AddressDTO.fromdict(dto)

        for precondition in self.__preconditions:
            if self.invoke_procedure(precondition.procedure, dto) != precondition.output:
                raise exceptions.PreconditionError(precondition.procedure)

        return rendition.AddressRendition(self, dto, abstract=abstract, fail_on_missing=fail_on_missing)

    @classmethod
    def register_procedure(cls, country, func_name):
        def decorator(func):
            cls.__procedures[country][func_name] = func

        return decorator

    def invoke_procedure(self, func_name, dto):
        return self.__procedures[self.country][func_name](dto)


def uk_format_1_test(value):
    return re.fullmatch("^[0-9]{1,4}[a-zA-Z]{0,2}([-/][0-9]{1,4}[a-zA-Z]{0,2})?$", value) is not None


@Template.register_procedure('GB', 'UK-SubBldgConcat')
def uk_sub_bldg_concat(dto):
    if dto.is_populated('U40.28'):
        sub_building_name = dto.get('U40.28')
        if re.fullmatch("^[a-zA-z]{1,2}$", sub_building_name) is not None:
            if not dto.is_populated('U40.26'):
                building_number = dto.get("U40.24") if dto.is_populated("U40.24") else ""
                dto.set('U40.28', None)
                dto.set('U40.24', f"{building_number}{sub_building_name}")
    return 'Done'


@Template.register_procedure('GB', 'UK-ReformatBldgName')
def uk_reformat_bldg_name(dto):
    APARTMENT_SUITE = (
        "APARTMENT", "APARTMENTS", "BLOCK", "BLOCKS", "FLAT", "FLATS", "HOUSE NUMBER", "HOUSE NUMBERS", "MAISONETTE",
        "MAISONETTES", "SHOP", "SHOPS", "STALL", "STALLS", "SUITE", "SUITES", "UNIT", "UNITS", "BACK OF", "REAR OF"
    )

    if dto.is_populated('U40.26') and not dto.is_populated('U40.24'):
        building_name = dto.get('U40.26')
        match = re.fullmatch("^(?P<name>.* )(?P<range>[0-9]{1,4}[a-zA-Z]{0,2}([-/][0-9]{1,4}[a-zA-Z]{0,2})?)$", building_name)
        if match is not None:
            building_name_upper = building_name.upper()
            if all(x not in building_name_upper for x in APARTMENT_SUITE):
                if re.fullmatch("^[0-9]{1,4}$", match.group('range')) is None:
                    name = match.group('name')
                    ra = match.group('range')
                    dto.set('U40.26', name.strip() if name else '')
                    dto.set('U40.24', ra.strip() if ra else '')

    return 'Done'


@Template.register_procedure('GB', 'UK-BldgNameFormat1Test')
def uk_reformat_bldg_name(dto):
    building_name = dto.get('U40.26')
    return 'Y' if uk_format_1_test(building_name) else 'N'


@Template.register_procedure('GB', 'UK-SubBldgNameFormat1Test')
def uk_reformat_sub_bldg_name(dto):
    sub_building_name = dto.get('U40.28')
    return 'Y' if uk_format_1_test(sub_building_name) else 'N'


@Template.register_procedure('US', 'US-RuralRouteTypeTest')
def us_rural_route_type_test(dto):
    if dto.is_populated('U40.24'):
        result = False
    elif dto.is_populated('U40.21-2-2'):
        result = False
    elif dto.is_populated('U40.21-1-1'):
        thoroughfare_name = dto.get('U40.21-1-1')
        result = re.match(r"^(RR|HC)\s[0-9].*", thoroughfare_name) is not None
    else:
        result = False

    assert result is not None
    return 'Y' if result else 'N'
