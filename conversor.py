import xml.etree.ElementTree as ET


class XMLElement(object):
    """Abstract Represents a xml element"""
    def __init__(self, tag, attrs={}, value=None):
        self.element = ET.Element(tag, attrs)
        if value:
            self.element.text = value


class Document(object):
    """Represents a data document, importable by tryton"""

    def __init__(self):
        self.tree = ET.ElementTree()
        self.root = ET.Element('tryton')
        self.data = ET.SubElement(self.root, 'data')
        self.tree._setroot(self.root)

    def add_record(self, record):
        """Adds a record on current tree"""
        self.data.append(record.element)

    def get_xml(self):
        return self.tree


class Field(XMLElement):
    """Represents a Field of tryton"""
    def __init__(self, name, attrs={}, value=None):
        attrs['name'] = name
        print value
        super(Field, self).__init__('field', attrs, value)


class Record(XMLElement):
    """Represents a record of a tryton model"""
    def __init__(self, model, id):
        attrs = {'model': model, 'id': id}
        super(Record, self).__init__('record', attrs)

    def add_field(self, field):
        """Ads a new field inside the record"""
        self.element.append(field.element)


if __name__ == '__main__':
    #TODO Write a test, you lazy programmer
    doc = Document()
    a = Record('account.account.type.template', 'ar')
    a.add_field(
        Field('name', value='Plan de cuentas argentino para cooperativas')
        )
    a.add_field(Field('sequence', {'eval': '10'}))
    doc.add_record(a)

    print ET.dump(doc.tree)
