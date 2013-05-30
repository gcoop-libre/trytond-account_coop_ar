# -*' coding: utf8 -*-

import csv
import xml.etree.ElementTree as ET

from unicodedata import normalize


def normalizar_string(unicode_string):
    u"""Retorna unicode_string normalizado para efectuar una búsqueda.

    >>> normalizar_string(u'Mónica Viñao')
    'monica vinao'

    """
    return normalize('NFKD', unicode_string).encode('ASCII', 'ignore').lower()


def sanitize(unicode_string):
    """cleanup an string, to use as id"""
    return normalizar_string(unicode_string).replace(' ', '_').replace('.', '')

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


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
        attrs = {'model': model, 'id': id,}
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
            'gastos': 'expense',
            }

    account_types = {}

    def __init__(self, types_file, account_file):
        self.account_file = account_file
        self.types_file = types_file
        self.document = Document()
        self.account_parents = {}

        self.record_ids = set()

    def inflate(self):
        """Make data grow up, because java
        programmers dont worry about storage"""

        with open(self.types_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.process_type_row(row)

        root = Record('account.account.template', 'root')
        root.add_field(Field('name',
            value='Plan Contable Argentino para Cooperativas'))
        root.add_field(Field('kind', value='view'))
        root.add_field(Field('type', {'ref': 'ar'}))
        self.document.add_record(root)

        with open(self.account_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.process_account_row(row)

        return self.document.tree

    def process_type_row(self, row):
        """Manages account type rows"""
        name = row['name'].decode('utf8')
        id = row['id']
        if not id:
            id = 'account_type_%s' % sanitize(name)

        self.account_types[name.lower()] = id

        record = Record('account.account.type.template', id)
        record.add_field(Field('name', value=name))
        record.add_field(Field('sequence', {'eval': row['sequence']}))
        if row['parent']:
            record.add_field(Field('parent', {'ref': row['parent']}))

        self.document.add_record(record)

    def process_account_row(self, row):
        #FIXME unicode
        group = row['GRUPO']
        code = row['NUMERO']
        kind = self.types[row['clase']]
        description = row['DESCRIPCION'].decode('utf8')

        id = sanitize(description)

        if id in self.record_ids:
            old_id = id
            id = '_'.join([id, code])
            print "Wups, looks like you have duplicated names using '%s' instead '%s'" % (id, old_id)

        if kind == 'view':
            code += '*'

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

        if kind != 'view':
            type = self.account_types[row['tipo']]
            record.add_field(Field('type', {'ref': type}))

        record.add_field(Field('parent', {'ref': parent}))

        self.document.add_record(record)

    def get_parent_for(self, group, id):
        """Return parent of a given group"""
        self.account_parents[group] = id
        if '.' in group:
            key = '.'.join(group.split('.')[:-1])
            return self.account_parents[key]
        else:
            return 'root'


if __name__ == '__main__':
    import xml.dom.minidom

    def imprimir_lindo(xml_string):
        tree = xml.dom.minidom.parseString(xml_string)
        return tree.toprettyxml(encoding='utf8')

    tipos = 'account_types.csv'
    cuentas = 'cuentas.csv'
    g = WierdXMLGenerator(tipos, cuentas)
    with open('accounts_coop_ar.xml', 'w') as fh:
        indent(g.inflate()._root)
        g.document.tree.write(fh, 'utf-8')
        #fh.write(indent(g.inflate()._root).tostring())
