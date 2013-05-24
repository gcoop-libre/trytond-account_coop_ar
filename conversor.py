# -*- coding: utf8 -*-

import csv
import xml.etree.ElementTree as ET

from unicodedata import normalize

def normalizar_string(unicode_string):
    u"""Retorna unicode_string normalizado para efectuar una búsqueda.

    >>> normalizar_string(u'Mónica Viñao')
    'monica vinao'

    """
    return normalize('NFKD', unicode_string).encode('ASCII', 'ignore').lower()

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
        super(Field, self).__init__('field', attrs, value)


class Record(XMLElement):
    """Represents a record of a tryton model"""
    def __init__(self, model, id):
        attrs = {'model': model, 'id': id}
        super(Record, self).__init__('record', attrs)

    def add_field(self, field):
        """Adds a new field inside the record"""
        self.element.append(field.element)


class WierdXMLGenerator(object):
    """Takes a csv and creates a lot of xml tags
    as java programmers like"""
    types = {
            'vista': 'view',
            'otro': 'other',
            'a pagar': 'payable',
            'a cobrar': 'receivable',
            'ingresos': 'revenue',
            'existencias': 'stock',
            'gastos':'expense',
            }

    def __init__(self, filename):
        self.filename = filename
        self.document = Document()
        self.parents = {}
        self.record_ids = set()

    def inflate(self):
        """Make data grow up, because java
        programmers dont worry about storage"""
        with open(self.filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.process_row(row)

        return self.document.tree

    def process_row(self, row):
        #FIXME unicode
        group = row['GRUPO']
        code = row['NUMERO']  # si tiene hijos, ponerle un *
        kind = self.types.get(row['clase'], '')
        print row
        description = row['DESCRIPCION'].decode('utf8')
        #FIXME ids con caracteres no ascii

        id = normalizar_string(description).replace(' ', '_')

        if id in self.record_ids:
            raise ValueError('You have defined this id twice motherfucker %s' % id)

        self.record_ids.add(id)

        parent = self.get_parent_for(group, id)
        record = Record('account.account.template', id)
        record.add_field(Field('name', value=description))
        record.add_field(Field('code', value=code))
        if row['aplazar']:
            record.add_field(Field('deferral', {'eval': 'True'}))

        if row['conciliar']:
            record.add_field(Field('reconcile', {'eval': 'True'}))

        record.add_field(Field('kind', value=kind))
        # Ver como manejar el valor de type
        #record.add_field(Field('type', value=code))

        record.add_field(Field('parent', {'ref': parent}))

        self.document.add_record(record)

    def get_parent_for(self, group, id):
        """Return parent of a given group"""
        self.parents[group] = id
        print group
        if '.' in group:
            key = '.'.join(group.split('.')[:-1])
            return self.parents[key]
        else:
            return 'root'


if __name__ == '__main__':
    import xml.dom.minidom

    def imprimir_lindo(xml_string):
        return xml.dom.minidom.parseString(xml_string).toprettyxml(encoding='utf8')

    FILENAME = 'cuentas.csv'
    g = WierdXMLGenerator(FILENAME)
    print imprimir_lindo(ET.tostring(g.inflate()._root))
