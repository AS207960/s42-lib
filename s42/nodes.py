import collections
import functools
import operator


class Node:
    name = "Node"

    @property
    def children(self):
        return self._children

    def __init__(self, template, dto):
        self.template = template
        self.dto = dto
        self.parent = None
        self.siblings = []
        self._children = []

    def is_element(self):
        return False

    def is_leaf(self):
        return bool(self.children)

    def is_empty(self):
        if self.is_element():
            return False

        for c in self.children:
            if c.is_element():
                return False
            if not c.is_empty():
                return False
        return True

    def is_rightmost(self):
        return self.siblings and (self.siblings[-1] == self)

    def render(self):
        if not self.children:
            return ''

        return functools.reduce(operator.add, self.children)\
            if (len(self.children) >= 1)\
            else self.children[0].render()

    def __str__(self):
        return self.render()

    def __repr__(self):
        if self.children:
            children = '\n-'.join(map(repr, self.children))
            children = f"-{children}"
            children = "\n".join(f"  {l}" for l in children.split("\n"))
            return f"<{self.name}>:\n{children}"
        else:
            return f"<{self.name}>"

    def add(self, node):
        node.parent = self
        node.siblings = self._children
        self._children.append(node)

    def __iter__(self):
        return iter(self.children)


class AddressNode(Node):
    name = "AddressNode"


class ComponentNode(Node):
    name = "ComponentNode"

    def __init__(self, template, dto, name):
        Node.__init__(self, template, dto)
        self.comp_id = name

    def __repr__(self):
        if self.children:
            children = '\n-'.join(map(repr, self.children))
            children = f"-{children}"
            children = "\n".join(f"  {line}" for line in children.split("\n"))
            return f"<{self.name}: {self.comp_id}>:\n{children}"
        else:
            return f"<{self.name}: {self.comp_id}>"


class LineNode(Node):
    name = "LineNode"

    def __init__(self, template, dto, name):
        Node.__init__(self, template, dto)
        self.line_id = name

    def __repr__(self):
        if self.children:
            children = '\n-'.join(map(repr, self.children))
            children = f"-{children}"
            children = "\n".join(f"  {line}" for line in children.split("\n"))
            return f"<{self.name}: {self.line_id}>:\n{children}"
        else:
            return f"<{self.name}: {self.line_id}>"

    @property
    def nodeseq(self):
        for component in self.children:
            for element in component:
                yield element

    def render(self):
        if not self.children:
            return ''

        output = ''
        nodes = list(self.nodeseq)
        last_node = None
        for node in nodes:
            if last_node and node.is_element():
                if isinstance(last_node, SeparatorNode):
                    output += last_node.value
                else:
                    output += ' '

            last_node = node
            if not node.is_element():
                continue
            output += str(node)

        return output


class SeparatorNode(Node):
    def __init__(self, template, dto, value):
        Node.__init__(self, template, dto)
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return "<SeparatorNode: {0}>".format(self.value or 'DEFAULT')


class ValueNode(Node):
    @property
    def value(self):
        return self.dto.get(self.code)

    def __init__(self, template, dto, code):
        Node.__init__(self, template, dto)
        self.code = code

    def is_element(self):
        return True

    def __str__(self):
        return self.value

    def __repr__(self):
        return "<ValueNode: {0}>".format(self.value)
