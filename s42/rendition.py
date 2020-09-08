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

    def __init__(self, template, dto, abstract=False, fail_on_missing=True, sep=None):
        self._template = template
        self._dto = dto
        self._abstract = abstract
        self._lines = None
        self._sep = os.linesep if not sep else sep
        self._fail = fail_on_missing

    def is_abstract(self):
        return self._abstract

    def _render(self,):
        self._candidates = copy.deepcopy(self._template.get_selected_lines(self._dto))

        self.migrate_lines()
        self.dedup_elements()
        self.remove_blank()
        if self._fail:
            self.validate_required()

        node = nodes.AddressNode(self._template, self._dto)
        for line in self._candidates:
            l_node = line.as_node(self._template, self._dto, self._fail)
            node.add(l_node)

        self._lines = node

    def __str__(self):
        return os.linesep.join(str(l) for l in self.lines if not l.is_empty())

    def __iter__(self):
        return iter(self.lines)

    def migrate_lines(self):
        migration_elements = {}

        for li, line in enumerate(self._candidates):
            for ci, component in enumerate(line.components):
                for ei, element in enumerate(component.elements):
                    if element.is_element and element.migration_precedence:
                        is_candidate = any(
                            (
                                self._dto.is_populated(e.code)
                                if e.code != element.code else False
                            ) for e in component.elements if e.is_element
                        )
                        if is_candidate:
                            preference = 1
                        else:
                            is_candidate = any(
                                (
                                    (self._dto.is_populated(e.code) if e.required else True)
                                    if e.code != element.code else False
                                ) for e in component.elements if e.is_element
                            )
                            if is_candidate:
                                preference = 2
                            else:
                                is_candidate = any(
                                    (
                                        (self._dto.is_populated(e.code) if e.required else True)
                                        if e.code != element.code else False
                                    ) for c in line.components for e in c.elements if e.is_element
                                )
                                preference = 3
                        data = {
                                "element": element,
                                "lines_index": li,
                                "component_index": ci,
                                "element_index": ei,
                                "is_candidate": is_candidate,
                                "preference": preference
                            }
                        if element.code in migration_elements:
                            migration_elements[element.code].append(data)
                        else:
                            migration_elements[element.code] = [data]

        for elements in migration_elements.values():
            if len(elements) > 1:
                elements.sort(key=lambda e: e["element"].migration_precedence)
                f_elements = list(filter(lambda e: e[1]["is_candidate"], enumerate(elements)))
                f_elements.sort(key=lambda e: e[1]["preference"])
                e = next(iter(f_elements), None)
                if e:
                    ce_i, chosen_element = e
                    for i, element in enumerate(elements):
                        if i != ce_i:
                            del self._candidates[
                                element["lines_index"]
                            ].components[
                                element["component_index"]
                            ].elements[
                                element["element_index"]
                            ]

    def dedup_elements(self):
        elements = {}

        for li, line in enumerate(self._candidates):
            for ci, component in enumerate(line.components):
                for ei, element in enumerate(component.elements):
                    if element.is_element:
                        data = {
                                "element": element,
                                "lines_index": li,
                                "component_index": ci,
                                "element_index": ei,
                            }
                        code = self._dto.get_code(element.code)
                        code = code if code else element.code
                        if code in elements:
                            elements[code].append(data)
                        else:
                            elements[code] = [data]

        for elements in elements.values():
            if len(elements) > 1:
                e = next(enumerate(elements), None)
                ce_i, chosen_element = e
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
            if not any(self._dto.is_populated(e.code) if not c.required and e.is_element else True for c in line.components for e in c.elements):
                removed_lines.append(i)

        offset = 0
        for i in removed_lines:
            del self._candidates[i-offset]
            offset += 1

    def validate_required(self):
        for line in self._candidates:
            for component in line.components:
                for element in component.elements:
                    if element.is_element and element.required and not self._dto.is_populated(element.code):
                        raise exceptions.RequiredElementError(element.code, str(line.identifier.symbolic))

                if component.required:
                    if not any(self._dto.is_populated(e.code) for e in component.elements):
                        raise exceptions.RequiredElementError(
                            list(map(lambda e: element.code, component.elements)),
                            str(line.identifier.symbolic)
                        )


