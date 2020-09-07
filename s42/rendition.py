from . import nodes, data, exceptions
import os
import copy


class AddressRendition:
    _dto: data.AddressDTO

    @property
    def lines(self):
        if self._lines is None:
            self._render()
        return self._lines

    def __init__(self, template, dto, abstract=False, sep=None):
        self._template = template
        self._dto = dto
        self._abstract = abstract
        self._lines = None
        self._sep = os.linesep if not sep else sep

    def is_abstract(self):
        return self._abstract

    def _render(self):
        self._candidates = copy.deepcopy(self._template.get_selected_lines(self._dto))

        self.migrate_lines()
        self.remove_blank()
        self.validate_required()

        node = nodes.AddressNode(self._template, self._dto)
        for line in self._candidates:
            l_node = line.as_node(self._template, self._dto)
            if bool(l_node.children):
                node.add(l_node)

        self._lines = node

    def __str__(self):
        return os.linesep.join(str(l) for l in self.lines)

    def __iter__(self):
        return iter(self.lines)

    def migrate_lines(self):
        migration_elements = {}

        for li, line in enumerate(self._candidates):
            for ci, component in enumerate(line.components):
                for ei, element in enumerate(component.elements):
                    if element.migration_precedence:
                        is_candidate = any(
                            (
                                self._dto.is_populated(e.code) if e.code != element.code else False
                            ) for e in component.elements
                        )
                        data = {
                                "element": element,
                                "lines_index": li,
                                "component_index": ci,
                                "element_index": ei,
                                "is_candidate": is_candidate
                            }
                        if element.code in migration_elements:
                            migration_elements[element.code].append(data)
                        else:
                            migration_elements[element.code] = [data]

        for elements in migration_elements.values():
            if len(elements) > 1:
                elements.sort(key=lambda e: e["element"].migration_precedence)
                ce_i, chosen_element = next(filter(lambda e: e[1]["is_candidate"], enumerate(elements)))

                for i, element in enumerate(elements):
                    if i != ce_i:
                        del self._candidates[
                            element["lines_index"]
                        ].components[
                            element["component_index"]
                        ].elements[
                            element["element_index"]
                        ]

    def remove_blank(self):
        removed_lines = []

        for i, line in enumerate(self._candidates):
            if not any(self._dto.is_populated(e.code) if not c.required else True for c in line.components for e in c.elements):
                removed_lines.append(i)

        offset = 0
        for i in removed_lines:
            del self._candidates[i-offset]
            offset += 1

    def validate_required(self):
        for line in self._candidates:
            for component in line.components:
                for element in component.elements:
                    if element.required and not self._dto.is_populated(element.code):
                        raise exceptions.RequiredElementError(element.code, str(line.identifier.symbolic))

                if component.required:
                    if not any(self._dto.is_populated(e.code) for e in component.elements):
                        raise exceptions.RequiredElementError(
                            list(map(lambda e: element.code, component.elements)),
                            str(line.identifier.symbolic)
                        )


