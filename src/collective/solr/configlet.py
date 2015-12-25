# -*- coding: utf-8 -*-
from plone.app.registry.browser import controlpanel
from collective.solr.interfaces import ISolrSchema, _


class SolrControlPanelForm(controlpanel.RegistryEditForm):

    id = "SolrControlPanel"
    label = _('label_solr_settings', default='Solr settings')
    schema = ISolrSchema
    schema_prefix = "collective.solr"


class SolrControlPanel(controlpanel.ControlPanelFormWrapper):

    form = SolrControlPanelForm
