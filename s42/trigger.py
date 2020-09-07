import dataclasses
import typing
import collections
import re
from . import data


@dataclasses.dataclass
class Trigger:
    conditions: typing.List
    lines: typing.List

    @classmethod
    def fromelements(cls, template, triggers, lines):
        args = collections.defaultdict(list)
        for element in triggers:
            args[element.tag].append(element)

        return Trigger(
            conditions=[TriggerCondition.factory(template, x, *y) for x, y in args.items()],
            lines=[data.LineIdentifier.from_xml(x) for x in lines]
        )

    def is_satisfied(self, dto):
        return all([x.is_satisfied(dto) for x in self.conditions])


@dataclasses.dataclass
class LineSelector:
    groups: typing.List[Trigger]

    @staticmethod
    def parse_line_triggers(template, element):
        # Trigger conditions are followed by one or more line candidates,
        # and if the conditions are satisfied, the immediately following
        # line candidates, which may explicitly include or implicitly
        # exclude line components, will be selected into the initial
        # rendition. Each line candidate and line component with all of
        # its elements and operators are defined in a lineData section.
        # Whenever one set of trigger conditions within a lineSelect block
        # has been satisfied, none of the others are evaluated. If a line
        # candidate is selected but user preferences indicate that it is
        # to be suppressed, it is not brought forward (NEN 2011: 47).

        groups = []
        new_group = True
        i = -1
        preceding_tag = None
        for child in element:
            tag = child.tag
            value = child.text
            assert tag in ['lineName'] + VALID_TRIGGER_CONDITIONS, tag

            if (preceding_tag == 'lineName') and (tag in VALID_TRIGGER_CONDITIONS):
                new_group = True

            if new_group:
                groups.append({'triggers': [], 'lines': []})
                i += 1
                new_group = False

            key = 'lines' if tag == 'lineName' else 'triggers'
            groups[i][key].append(child)

            preceding_tag = tag

        return LineSelector._groups_from_elements(template, groups)

    @staticmethod
    def _groups_from_elements(template, groups):
        return [Trigger.fromelements(template, **x) for x in groups]

    @classmethod
    def from_xml(cls, template, element):
        return cls(cls.parse_line_triggers(template, element))

    def get_lines(self, dto):
        lines = []
        for trigger in self.groups:
            if trigger.is_satisfied(dto):
                return trigger.lines

        return lines


@dataclasses.dataclass
class TriggerCondition:
    args: typing.Optional[typing.List]
    template: object

    @staticmethod
    def parse_arg(template, element):
        raise NotImplementedError("Subclasses must override this method.")

    @staticmethod
    def factory(template, tag, *args):
        return TRIGGER_CONDITION_MAPPING[tag].fromelements(template, *args)

    @classmethod
    def fromelements(cls, template, *elements):
        return cls(template=template, args=[cls.parse_arg(template, x) for x in elements])

    def is_satisfied(self, dto):
        return all(map(lambda x: self.process_arg(dto, *x), self.args))


class DefaultCase(TriggerCondition):
    @classmethod
    def fromelements(cls, template, *elements):
        return cls(template=template, args=None)

    def is_satisfied(self, value):
        return True


class IsPopulated(TriggerCondition):
    @staticmethod
    def parse_arg(template, element):
        return [
            list(map(str.strip, x.split(template.separator))) for x in
            map(str.strip, element.text.split(template.sequencer))
        ]

    def process_arg(self, dto, *codes):
        is_satisfied = False
        for codeset in codes:
            is_satisfied |= all(map(dto.is_populated, codeset))

        return is_satisfied


class IsNotPopulated(TriggerCondition):
    @staticmethod
    def parse_arg(template, element):
        return [
            list(map(str.strip, x.split(template.separator))) for x in
            map(str.strip, element.text.split(template.sequencer))
        ]

    def process_arg(self, dto, *codes):
        is_satisfied = False
        for codeset in codes:
            is_satisfied |= not any(map(dto.is_populated, codeset))

        return is_satisfied


class HasValue(TriggerCondition):
    @staticmethod
    def parse_arg(template, element):
        return list(map(lambda x: x.strip().strip('"'), element.text.split(template.separator)))

    def process_arg(self, dto, code, value):
        return dto.get(code) == value


class HasResult(TriggerCondition):
    @staticmethod
    def parse_arg(template, element):
        return list(map(lambda x: str.strip(x).strip('"'), element.text.split(template.separator)))

    def process_arg(self, dto, func, retval):
        return self.template.invoke_procedure(func, dto) == retval


class MatchesRegex(TriggerCondition):
    @staticmethod
    def parse_arg(template, element):
        args = list(map(lambda x: x.strip().strip('"'), element.text.split(template.separator)))
        args[1] = re.compile(args[1])
        return args

    def process_arg(self, dto, code, regex):
        return regex.fullmatch(dto.get(code)) is not None


TRIGGER_CONDITION_MAPPING = {
    'defaultCase': DefaultCase,
    'hasValue': HasValue,
    'isPopulated': IsPopulated,
    'isNotPopulated': IsNotPopulated,
    'hasResult': HasResult,
    'matchesRegex': MatchesRegex,
}


VALID_TRIGGER_CONDITIONS = list(TRIGGER_CONDITION_MAPPING.keys())


@dataclasses.dataclass
class Precondition:
    procedure: str
    output: str
    template: object

    @classmethod
    def from_xml(cls, template, element):
        args = list(map(lambda x: x.strip().strip('"'), element.text.split(template.separator)))
        return cls(
            procedure=args[0],
            output=args[1],
            template=template
        )
