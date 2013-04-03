# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi KK and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from Products.ERP5Type.Interactor.Interactor import Interactor
from Products.ERP5.ERP5Site import getSite

class DeliveryInventoryInteractor(Interactor):
  """
    Reindex the equivalent inventory when you are adding (correction) movements
    AFTER inventory stock taking.
  """

  def install(self):
    from Products.ERP5.Document.Delivery import Delivery
    self.on(Delivery.reindexObject).doAfter(self.reindexLatestInventory)

  def reindexLatestInventory(self, method_call_object, *args, **kw):
    delivery = method_call_object.instance
    # only when it is enabled thereby it should not be so harmful on performance
    if self._isNoUse(delivery):
      return
    # find later inventory than the movement
    inventory_set = set()
    for movement in delivery.getMovementList():
      found_inventory_set = self._findLaterInventorySet(delivery, movement)
      if not found_inventory_set:
        continue
      inventory_set.update(found_inventory_set)
    if not inventory_set:
      return
    # if exists, reindex it
    activate_kw = dict(
      priority=4,
      after_path_and_method_id=(delivery.getPath(),
                                ['_updateSimulation',
                                 'immediateReindexObject',
                                 'recursiveImmediateReindexObject']))
    for inventory in inventory_set:
      inventory.activate(**activate_kw).immediateReindexObject()

  def _isNoUse(self, delivery):
    portal = getSite()
    preference = portal.portal_preferences
    try:
      if not preference.getPreferredReindexInventoryWhenAddingPreviousMovement():
        return True
    except AttributeError:
      return True
    bt_list = portal.portal_templates.getInstalledBusinessTemplateTitleList()
    if 'erp5_movement_table_catalog' not in bt_list:
      raise EnvironmentError, 'You need to install ' \
       'erp5_movement_table_catalog business template when you enable:' \
       "'Reindex Inventory When Adding Previous Movement' flag"
    # XXX-Tatuya: only when 'delivered'. Is this enough for all use-cases?
    if delivery.getSimulationState() != 'delivered':
      return True
    if not delivery.isAccountable():
      return True
    # Ignore myself
    if delivery.getPortalType() in delivery.getPortalInventoryTypeList():
      return True
    return False

  def _findLaterInventorySet(self, delivery, movement):
    """ Handle the node_uid and section_uid difference by the portal type """
    source_uid = delivery.getSourceUid()
    source_section_uid = delivery.getSourceSectionUid()
    destination_uid = delivery.getDestinationUid()
    destination_section_uid = delivery.getDestinationSectionUid()
    find_set = set()
    find = self._findLaterInventory
    if delivery.getPortalType() in ('Sale Order', 'Returned Purchase Order'):
      find_set.add(find(source_uid, source_section_uid, movement))
    elif delivery.getPortalType() in ('Purchase Order', 'Returned Sale Order'):
      find_set.add(find(destination_uid, destination_section_uid, movement))
    else:
      # 'Internal Packing List' and other cases
      find_set.add(find(source_uid, source_section_uid, movement))
      find_set.add(find(destination_uid, destination_section_uid, movement))
    return set([x for x in find_set if x is not None])

  def _findLaterInventory(self, node_uid, section_uid, movement):
    """ find later inventory than the movement"""
    if node_uid is None or section_uid is None:
      return None
    params = {'portal_type':movement.getPortalInventoryMovementTypeList(),
              'explanation_destination_section_uid':section_uid,
              'movement.start_date':'>%s' % movement.getStartDate(),
              'movement.destination_uid':node_uid,
              'movement.resource_uid':movement.getResourceUid(),
              'movement.variation_text':movement.getVariationText()}
    portal = getSite()
    result = portal.portal_catalog(
      limit=2, # The latest must be only 1 but use limit=2 for checking.
      sort_on=[('movement.start_date', 'ascending'), ('uid', 'ascending')],
      **params)

    if len(result) == 0:
      return None
    if len(result) == 1:
      return result[0].getObject().getRootDeliveryValue()
    elif len(result) >= 2:
      if result[0].getObject().getStartDate() == result[1].getObject().getStartDate():
        raise RuntimeError("Inventories are duplicated: %s and %s"
                           % (result[0].getPath(), result[1].getPath()))

