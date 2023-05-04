# -*- coding: utf-8 -*-
import logging

from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrSchema
from plone import api
from plone.registry.interfaces import IRegistry

logger = logging.getLogger('collective.solr')
PROFILE_ID = 'profile-collective.solr:default'


@implementer(INonInstallable)
class HiddenProfiles(object):

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation"""
        return [
            'collective.solr:uninstall',
        ]


def migrateTo2(context):
    setup_tool = getToolByName(context, 'portal_setup')
    setup_tool.runImportStepFromProfile(PROFILE_ID, 'browserlayer')
    logger.info('Migrated to version 2: add browserlayer')


def update_registry(context):
    registry = getUtility(IRegistry)
    util = queryUtility(ISolrConnectionConfig)
    if util is not None:
        # Preferably we would get the previous data from this utility, so we
        # can restore the settings.  But the utility is broken.  The best we
        # can do, is remove it.
        sm = getSiteManager()
        sm.unregisterUtility(provided=ISolrConnectionConfig)

    registry.registerInterface(ISolrSchema, prefix='collective.solr')


def unregister_utility(context, iface, name=None):
    sm = context.getSiteManager()
    if name:
        # for named utility
        util = sm.queryUtility(iface, name)
        sm.unregisterUtility(component=util, provided=iface, name=name)
    else:
        # for unnamed utility
        util = sm.queryUtility(iface)
        sm.unregisterUtility(provided=iface)
        sm.utilities.unsubscribe((), iface)
    if util:
        del util
    if iface in sm.utilities.__dict__['_provided']:
        del sm.utilities.__dict__['_provided'][iface]
    if iface in sm.utilities._subscribers[0]:
        del sm.utilities._subscribers[0][iface]
    sm.utilities._p_changed = True


def post_uninstall(context):
    portal = api.portal.get()
    utils_to_unregister = (
        (ISearch, None),
        (ISolrIndexQueueProcessor, 'solr'),
        (ISolrConnectionManager, None)
    )
    for iface, name in utils_to_unregister:
        try:
            unregister_utility(portal, iface, name)
        except Exception:
            logger.debug("Can't unregister utility: %s/%s" % (iface, name))
