##############################################################################
#
# Copyright (c) 2002-2005 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
#                    Romain Courteaud <romain@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
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

from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions, PropertySheet, Constraint, Interface
from Products.ERP5.Document.Rule import Rule
from Products.ERP5.Document.DeliveryRule import DeliveryRule

from zLOG import LOG

class InvoiceRule(DeliveryRule):
    """
      InvoiceRule and DeliveryRule seems to be identical.
      Keep it for compatibility only.
    """

    # CMF Type Definition
    meta_type = 'ERP5 Invoice Rule'
    portal_type = 'Invoice Rule'
    add_permission = Permissions.AddPortalContent
    isPortalContent = 1
    isRADContent = 1

    # Declarative security
    security = ClassSecurityInfo()
    security.declareObjectProtected(Permissions.View)

    # Default Properties
    property_sheets = ( PropertySheet.Base
                      , PropertySheet.XMLObject
                      , PropertySheet.CategoryCore
                      , PropertySheet.DublinCore
                      )

    # Simulation workflow
    security.declareProtected(Permissions.ModifyPortalContent, 'expand')
    def expand(self, applied_rule, 
               movement_type_method='getPortalInvoiceMovementTypeList', **kw):
      """
        Call expand defined on DeliveryRule.
      """
      DeliveryRule.expand(self, applied_rule, 
                          movement_type_method=movement_type_method,
                          **kw)
