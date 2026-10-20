"""Strict schema and reference handling for exported Instruments evidence."""


class XmlTable:
    def __init__(self, tree, columns):
        if [node.text for node in tree.findall('./node/schema/col/mnemonic')] != columns:
            raise ValueError('exact XML table schema required')
        self.tree, self.columns, self.identifiers = tree, columns, {}
        for node in tree.iter():
            identifier = node.get('id')
            if identifier:
                if identifier in self.identifiers:
                    raise ValueError('duplicate XML identifier')
                self.identifiers[identifier] = node

    def resolve(self, node):
        if node is None:
            raise ValueError('missing XML field')
        reference = node.get('ref')
        if not reference:
            return node
        if reference not in self.identifiers:
            raise ValueError('missing XML reference')
        return self.identifiers[reference]

    def rows(self):
        for row in self.tree.findall('./node/row'):
            if len(row) != len(self.columns):
                raise ValueError('incomplete XML row')
            yield [self.resolve(node) for node in row]
