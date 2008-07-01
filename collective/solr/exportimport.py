from zope.component import getUtility
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase

from collective.solr.interfaces import ISolrConnectionConfig


class SolrConfigXMLAdapter(XMLAdapterBase):

    _LOGGER_ID = 'collective.solr'

    def _exportNode(self):
        """ export the object as a DOM node """
        node = self._extractProperties()
        self._logger.info('settings exported.')
        return node

    def _importNode(self, node):
        """ import the object from the DOM node """
        if self.environ.shouldPurge():
            self._purgeProperties()
        self._initProperties(node)
        self._logger.info('settings imported.')

    def _purgeProperties(self):
        self.context.active = False
        self.context.host = ''
        self.context.port = 0
        self.context.base = ''
        self.context.async = False

    def _initProperties(self, node):
        conn = node.getElementsByTagName('connection')[0]
        for child in conn.childNodes:
            if child.nodeName == 'active':
                value = self._convertToBoolean(str(child.getAttribute('value')))
                self.context.active = value
            elif child.nodeName == 'port':
                value = int(str(child.getAttribute('value')))
                self.context.port = value
            elif child.nodeName == 'host':
                self.context.host = str(child.getAttribute('value'))
            elif child.nodeName == 'base':
                self.context.base = str(child.getAttribute('value'))
        settings = node.getElementsByTagName('settings')[0]
        for child in settings.childNodes:
            if child.nodeName == 'async':
                value = self._convertToBoolean(str(child.getAttribute('value')))
                self.context.async = value

    def _createNode(self, name, value):
        node = self._doc.createElement(name)
        node.setAttribute('value', value)
        return node

    def _extractProperties(self):
        node = self._doc.createElement('object')
        node.setAttribute('name', 'solr')
        conn = self._doc.createElement('connection')
        node.appendChild(conn)
        conn.appendChild(self._createNode('active', str(bool(self.context.active))))
        conn.appendChild(self._createNode('host', self.context.host))
        conn.appendChild(self._createNode('port', str(self.context.port)))
        conn.appendChild(self._createNode('base', self.context.base))
        settings = self._doc.createElement('settings')
        node.appendChild(settings)
        settings.appendChild(self._createNode('async', str(bool(self.context.async))))
        return node


def importSolrSettings(context):
    """ import settings for solr integration from an XML file """
    site = context.getSite()
    utility = getUtility(ISolrConnectionConfig, context=site)
    importObjects(utility, '', context)


def exportSolrSettings(context):
    """ export settings for solr integration as an XML file """
    site = context.getSite()
    utility = getUtility(ISolrConnectionConfig, context=site)
    if utility is None:
        logger = context.getLogger('collective.solr')
        logger.info('Nothing to export.')
        return
    exportObjects(utility, '', context)

