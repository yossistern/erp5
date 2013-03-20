# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
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
"""
    ERP5Catalog provides an extended catalog based on ZSQLCatalog
    and extended local roles management
"""

import sys, Permissions, os
from App.Common import package_home
this_module = sys.modules[ __name__ ]
product_path = package_home( globals() )
this_module._dtmldir = os.path.join( product_path, 'dtml' )
# Update ERP5 Globals
from Products.ERP5Type.Utils import initializeProduct, updateGlobals

document_classes = updateGlobals(this_module, globals(),
                                 permissions_module=Permissions)

def initialize( context ):
  # Import Product Components
  from Tool import SynchronizationTool
  import Document
  # Define documents, classes, constructors and tools
  object_classes = ()
  content_constructors = ()
  content_classes = ()
  portal_tools = (SynchronizationTool.SynchronizationTool,)
  # Do initialization step
  initializeProduct(context, this_module, globals(),
                    document_module=Document,
                    document_classes=document_classes,
                    object_classes=object_classes,
                    portal_tools=portal_tools,
                    content_constructors=content_constructors,
                    content_classes=content_classes)
