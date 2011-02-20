from zope.component import adapts
from zope.interface import Interface, implements
from zope.interface.interfaces import IInterface
from zope import schema
from z3c.form import form, field


class ISalesforceMetadata(Interface):
    
    # XXX update fields options on change via AJAX
    sf_obj_type = schema.Choice(
        title = u'Salesforce object type',
        vocabulary = 'collective.salesforce.behavior.SObjectTypes',
        )

    # XXX use TALES expression
    criteria = schema.ASCIILine(
        title = u'Query Criteria',
        description = u'This will form the WHERE clause of the SOQL expression used '
                      u'to retrieve objects from Salesforce. Leave blank to include '
                      u'all objects of the given type.',
        required = False,
        )
    
    # XXX use content tree widget
    container = schema.ASCIILine(
        title = u'Container',
        description = u'Determines where items of this type will be placed when '
                      u'loading objects from Salesforce. May be a path relative '
                      u'to the portal root, or the name of a method on the content '
                      u'class which will be called to determine the container.',
        )

    fields = schema.Set(
        title = u'Fields',
        description = u'Select the fields you want to load from Salesforce. '
                      u'New fields will be added to the content type if necessary '
                      u'when you save this form.',
        value_type = schema.Choice(
            vocabulary = 'collective.salesforce.behavior.SObjectFields',
            ),
        required = False,
        )


class TaggedValueScalarProperty(object):
    
    def __init__(self, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        return obj.context.queryTaggedValue(self.name)
    
    def __set__(self, obj, value):
        obj.context.setTaggedValue(self.name, value)


class SalesforceMetadataAdapter(object):
    implements(ISalesforceMetadata)
    adapts(IInterface)

    def __init__(self, context):
        self.context = context

    @property
    def sf_obj_type(self):
        return self.context.queryTaggedValue('salesforce.object')
    @sf_obj_type.setter
    def sf_obj_type(self, value):
        self.context.setTaggedValue('salesforce.object', value)
        # clear field mapping
        self.context.setTaggedValue('salesforce.fields', {})
    
    criteria = TaggedValueScalarProperty('salesforce.criteria')
    container = TaggedValueScalarProperty('salesforce.container')

    @property
    def fields(self):
        mapping = self.context.queryTaggedValue('salesforce.fields', {})
        return mapping.keys()
    @fields.setter
    def fields(self, value):
        mapping = self.context.queryTaggedValue('salesforce.fields', {})
        current = set(mapping)
        added = value - current
        removed = current - value
        for fname in added:
            mapping[fname] = fname
            # XXX create field
        for fname in removed:
            del mapping[fname]
        self.context.setTaggedValue('salesforce.fields', mapping)


class SalesforceMetadataForm(form.EditForm):
    label = u'Salesforce Object Settings'
    fields = field.Fields(ISalesforceMetadata)
    
    # Use the schema as the form context. When the form is saved, the schema
    # will be adapted to ISalesforceMetadata to get a SalesforceMetadataAdapter
    # to write the values; then an object modified event will be raised on
    # the schema to trigger its serialization.
    def getContent(self):
        return self.context.schema