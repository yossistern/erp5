##############################################################################
#
# Copyright (c) 2002 Nexedi SARL and Contributors. All Rights Reserved.
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

from Products.CMFCore.Expression import Expression

class Arrow:
    """
        Properties which allow to define a generic Arrow. Arrows are
        used by Path and Movements to define a source and a destination
        with attributes (payment, decision, etc.) which allow to qualify
        a movement
    """

    _properties = (
        # Source reference
        {   'id'          : 'source_title',
            'description' : 'The title of the source of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_id',
            'description' : 'The id of the destination of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_relative_url',
            'description' : 'The titles of the destination of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceRelativeUrl', ),
            'mode'        : 'w' },
        {   'id'          : 'source_person_title',
            'description' : 'The title of the source person of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source',),
            'acquisition_portal_type'       : ('Person'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'r' },
        {   'id'          : 'source_organisation_title',
            'description' : 'The title of the source organisation of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source',),
            'acquisition_portal_type'       : ('Organisation'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'r' },
        # Destination reference
        {   'id'          : 'destination_title',
            'description' : 'The title of the destination of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_id',
            'description' : 'The id of the destination of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_relative_url',
            'description' : 'The titles of the destination of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationRelativeUrl', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_person_title',
            'description' : 'The title of the destination person of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination',),
            'acquisition_portal_type'       : ('Person'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'r' },
        {   'id'          : 'destination_organisation_title',
            'description' : 'The title of the destination organisation of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination',),
            'acquisition_portal_type'       : ('Organisation'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'r' },
        # Source decision reference
        {   'id'          : 'source_decision_title',
            'description' : 'The title of the source decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceDecisionTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_decision_id',
            'description' : 'The id of the source decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceDecisionId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_decision_relative_url',
            'description' : 'The titles of the source decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceDecisionRelativeUrl', ),
            'mode'        : 'w' },
        # Destination decision reference
        {   'id'          : 'destination_decision_title',
            'description' : 'The title of the destination decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationDecisionTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_decision_id',
            'description' : 'The id of the destination decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationDecisionId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_decision_relative_url',
            'description' : 'The titles of the destination decision of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_decision',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationDecisionRelativeUrl', ),
            'mode'        : 'w' },
        # Source section reference
        {   'id'          : 'source_section_title',
            'description' : 'The title of the source section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceSectionTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_section_id',
            'description' : 'The id of the source section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceSectionId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_section_relative_url',
            'description' : 'The titles of the source section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceSectionRelativeUrl', ),
            'mode'        : 'w' },
        # Destination section reference
        {   'id'          : 'destination_section_title',
            'description' : 'The title of the destination section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationSectionTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_section_id',
            'description' : 'The id of the destination section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationSectionId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_section_relative_url',
            'description' : 'The titles of the destination section of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_section',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationSectionRelativeUrl', ),
            'mode'        : 'w' },
        # Source administration reference
        {   'id'          : 'source_administration_title',
            'description' : 'The title of the source administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceAdministrationTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_administration_id',
            'description' : 'The id of the source administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceAdministrationId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_administration_relative_url',
            'description' : 'The titles of the source administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceAdministrationRelativeUrl', ),
            'mode'        : 'w' },
        # Destination administration reference
        {   'id'          : 'destination_administration_title',
            'description' : 'The title of the destination administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationAdministrationTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_administration_id',
            'description' : 'The id of the destination administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationAdministrationId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_administration_relative_url',
            'description' : 'The titles of the destination administration of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_administration',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'alt_accessor_id'               : ('_categoryGetDestinationAdministrationRelativeUrl', ),
            'acquisition_depends'           : None,
            'mode'        : 'w' },
        # Source payment reference
        {   'id'          : 'source_payment_title',
            'description' : 'The title of the source payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourcePaymentTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_payment_id',
            'description' : 'The id of the source payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourcePaymentId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_payment_relative_url',
            'description' : 'The titles of the source payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourcePaymentRelativeUrl', ),
            'mode'        : 'w' },
        # Destination payment reference
        {   'id'          : 'destination_payment_title',
            'description' : 'The title of the destination payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationPaymentTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_payment_id',
            'description' : 'The id of the destination payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationPaymentId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_payment_relative_url',
            'description' : 'The titles of the destination payment of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_payment',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalNodeTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationPaymentRelativeUrl', ),
            'mode'        : 'w' },
        # more properties to make the difference between person and organisation
        {   'id'          : 'destination_decision_person_title',
            'description' : 'The title of the destination decision person of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_decision',),
            'acquisition_portal_type'       : 'Person',
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'w' },
        {   'id'          : 'destination_decision_organisation_title',
            'description' : 'The title of the destination decision organisation of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_decision',),
            'acquisition_portal_type'       : 'Organisation',
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'w' },
        {   'id'          : 'destination_administration_person_title',
            'description' : 'The title of the destination administration person of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_administration',),
            'acquisition_portal_type'       : 'Person',
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'w' },
        {   'id'          : 'destination_administration_organisation_title',
            'description' : 'The title of the destination administration organisation of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_administration',),
            'acquisition_portal_type'       : 'Organisation',
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'mode'        : 'w' },
        # Source project reference
        {   'id'          : 'source_project_title',
            'description' : 'The title of the source project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceProjectTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_project_id',
            'description' : 'The id of the source project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceProjectId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_project_relative_url',
            'description' : 'The titles of the source project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceProjectRelativeUrl', ),
            'mode'        : 'w' },
        # Destination project reference
        {   'id'          : 'destination_project_title',
            'description' : 'The title of the destination project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationProjectTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_project_id',
            'description' : 'The id of the destination project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationProjectId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_project_relative_url',
            'description' : 'The titles of the destination project of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_project',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationProjectRelativeUrl', ),
            'mode'        : 'w' },
        # Source budget reference
        {   'id'          : 'source_budget_title',
            'description' : 'The title of the source budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceBudgetTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'source_budget_id',
            'description' : 'The id of the source budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceBudgetId', ),
            'mode'        : 'w' },
        {   'id'          : 'source_budget_relative_url',
            'description' : 'The titles of the source budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('source_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetSourceBudgetRelativeUrl', ),
            'mode'        : 'w' },
        # Destination budget reference
        {   'id'          : 'destination_budget_title',
            'description' : 'The title of the destination budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getTitle',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationBudgetTitle', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_budget_id',
            'description' : 'The id of the destination budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getId',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationBudgetId', ),
            'mode'        : 'w' },
        {   'id'          : 'destination_budget_relative_url',
            'description' : 'The titles of the destination budget of this movement',
            'type'        : 'string',
            'acquisition_base_category'     : ('destination_budget',),
            'acquisition_portal_type'       : Expression('python: portal.getPortalOrderTypeList()'),
            'acquisition_copy_value'        : 0,
            'acquisition_accessor_id'       : 'getRelativeUrl',
            'acquisition_depends'           : None,
            'alt_accessor_id'               : ('_categoryGetDestinationBudgetRelativeUrl', ),
            'mode'        : 'w' },
   )

    _categories = ( 'source', 'destination',
                    'source_section', 'destination_section',
                    'source_decision', 'destination_decision',
                    'source_administration', 'destination_administration',
                    'source_payment', 'destination_payment',
                    'source_project', 'destination_project',
                    'source_budget', 'destination_budget',
                    # Virtual categories
                    'source_region', 'destination_region',
                    )

