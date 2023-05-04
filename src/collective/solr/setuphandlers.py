# -*- coding: utf-8 -*-

import logging

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrSchema
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer

logger = logging.getLogger("collective.solr")
PROFILE_ID = "profile-collective.solr:default"


@implementer(INonInstallable)
class HiddenProfiles(object):

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation"""
        return [
            'collective.solr:uninstall',
        ]


def migrateTo2(context):
    setup_tool = getToolByName(context, "portal_setup")
    setup_tool.runImportStepFromProfile(PROFILE_ID, "browserlayer")
    logger.info("Migrated to version 2: add browserlayer")


def update_registry(context):
    registry = getUtility(IRegistry)
    util = queryUtility(ISolrConnectionConfig)
    if util is not None:
        # Preferably we would get the previous data from this utility, so we
        # can restore the settings.  But the utility is broken.  The best we
        # can do, is remove it.
        sm = getSiteManager()
        sm.unregisterUtility(provided=ISolrConnectionConfig)

    registry.registerInterface(ISolrSchema, prefix="collective.solr")


def migrateTo4(context):
    registry = getUtility(IRegistry)
    if "collective.solr.async" in registry.records:
        old_record = registry.records["collective.solr.async"]
        registry.records["collective.solr.async_indexing"] = old_record
        del registry.records["collective.solr.async"]
        logger.info("Migrated to async_indexing setting")

    pt = api.portal.get_tool("portal_types")
    type_ids = (
        "Collection",
        "Document",
        "Event",
        "File",
        "Folder",
        "Image",
        "Link",
        "News Item",
    )
    new_behavior = "collective.solr.behaviors.ISolrFields"
    for type_id in type_ids:
        if type_id not in pt.objectIds():
            continue
        fti = pt[type_id]
        if new_behavior not in fti.behaviors:
            fti.behaviors += (new_behavior,)
            logger.info("Added new behavior to {}".format(type_id))

    logger.info("Migrated to version 4")


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
