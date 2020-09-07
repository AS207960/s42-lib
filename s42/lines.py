import dataclasses
import typing
from . import data, nodes


@dataclasses.dataclass
class Line:
    components: typing.List
    identifier: data.LineIdentifier

    @classmethod
    def from_xml(cls, element):
        identifier = data.LineIdentifier.from_xml(element.findall('./lineName')[0])

        components = []
        for child in element.findall('./lineComponent'):
            components.append(LineComponent.from_xml(child))

        return cls(identifier=identifier, components=components)

    def as_node(self, template, dto):
        node = nodes.LineNode(template, dto)
        for component in self.get_valid_components(dto):
            c_node = component.as_node(template, dto)
            if bool(c_node.children):
                node.add(c_node)

        return node

    def get_valid_components(self, dto):
        return [c for c in self.components if c.is_valid(dto)]


@dataclasses.dataclass
class LineComponent:
    component_id: str
    elements: typing.List
    priority: int
    required: bool = False

    Empty = type('Empty', (ValueError,), {})
    Missing = type('Missing', (ValueError,), {})

    @property
    def required_elements(self):
        return [x.code for x in self.elements if x.required]

    def is_valid(self, dto):
        return all([dto.is_populated(x) for x in self.required_elements])

    @classmethod
    def from_xml(cls, element):
        elements = []
        kwargs = {}
        for child in element:
            tag = child.tag
            value = child.text
            if tag == 'elementData':
                elements.append(ElementData.fromxml(child))
            elif tag == 'componentId':
                kwargs['component_id'] = value
            elif tag == 'requiredIfSelected':
                kwargs['required'] = value == 'Y'
            elif tag == 'priority':
                kwargs['priority'] = int(value)
            elif tag == 'renditionOperator':
                elements[-1].set_succeeding_rendition_operator(RenditionOperator.fromxml(child))
            else:
                raise NotImplementedError("Unrecognized tag: " + tag)

        kwargs['elements'] = elements
        return cls(**kwargs)

    def as_node(self, template, dto):
        node = nodes.ComponentNode(template, dto)

        for element in self.elements:
            if not dto.is_populated(element.code):
                continue
            node.add(element.as_node(template, dto))
        return node


@dataclasses.dataclass
class RenditionOperator:
    operator_type: str
    text: typing.Optional[str] = None
    justify: typing.Optional[str] = None

    CONCAT = 'CONCAT'

    @classmethod
    def fromxml(cls, element):
        kwargs = {}
        for child in element:
            tag = child.tag
            value = child.text
            if tag == 'operatorId':
                kwargs['operator_type'] = value
            elif tag == 'fldJustify':
                kwargs['justify'] = value
            elif tag == 'fldText':
                kwargs['text'] = value.strip("'")
            else:
                raise NotImplementedError("Unrecognized tag: " + tag)

        return cls(**kwargs)


@dataclasses.dataclass
class ElementData:
    code: str
    name: str
    required: bool = False
    justify: str = 'L'
    position: typing.Optional[str] = None
    migration_precedence: typing.Optional[int] = None
    succeeding_operator: typing.Optional[str] = None

    @classmethod
    def fromxml(cls, element):
        kwargs = {
        }
        for child in element:
            value = child.text
            tag = child.tag
            if tag == 'elementId':
                kwargs['code'] = data.Code.fromstring(value)
            elif tag == 'elementDef':
                kwargs['name'] = value
            elif tag == 'fldJustify':
                kwargs['justify'] = value
            elif tag == 'posStart':
                kwargs['position'] = value
            elif tag == 'requiredIfSelected':
                kwargs['required'] = value == 'Y'
            elif tag == 'migrationPrecedence':
                kwargs['migration_precedence'] = int(value)
            elif tag == 'elementDesc':
                # Description of the element. Currently not used.
                pass
            else:
                raise NotImplementedError("Unrecognized tag: " + tag)
        return cls(**kwargs)

    def as_node(self, template, dto):
        node = nodes.ElementNode(template, dto)
        node.add(nodes.ValueNode(template, dto, self.code))
        node.add(nodes.SeparatorNode(template, dto, self.get_succeeding_separator()))
        return node

    def get_preceding_separator(self):
        return ''

    def get_succeeding_separator(self):
        return ' ' if not self.succeeding_operator\
            else str(self.succeeding_operator)

    def add_to_line(self, parts, value):
        parts.extend([value, self.get_succeeding_separator()])
