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

import socket
import urllib
import threading
import sys
from types import StringType
import re
from cPickle import dumps, loads
from Products.CMFCore import permissions as CMFCorePermissions
from Products.ERP5Type.Core.Folder import Folder
from Products.CMFActivity.ActiveResult import ActiveResult
from Products.CMFActivity.ActiveObject import DEFAULT_ACTIVITY
from Products.CMFActivity.ActivityConnection import ActivityConnection
from Products.PythonScripts.Utility import allow_class
from AccessControl import ClassSecurityInfo, Permissions
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import getSecurityManager
from Products.CMFCore.utils import UniqueObject, _getAuthenticatedUser
from Products.ERP5Type.Globals import InitializeClass, DTMLFile
from Acquisition import aq_base, aq_inner, aq_parent
from ActivityBuffer import ActivityBuffer
from ActivityRuntimeEnvironment import BaseMessage
from zExceptions import ExceptionFormatter
from BTrees.OIBTree import OIBTree
from zope.site.hooks import setSite

try:
  from Products import iHotfix
  localizer_lock = iHotfix._the_lock
  localizer_contexts = iHotfix.contexts
  LocalizerContext = iHotfix.Context
except ImportError:
  # Localizer 1.2 includes iHotFix patches
  import Products.Localizer.patches
  localizer_lock = Products.Localizer.patches._requests_lock
  localizer_contexts = Products.Localizer.patches._requests
  LocalizerContext = lambda request: request


from ZODB.POSException import ConflictError
from Products.MailHost.MailHost import MailHostError

from zLOG import LOG, INFO, WARNING, ERROR
from warnings import warn
from time import time

try:
  from Products.TimerService import getTimerService
except ImportError:
  def getTimerService(self):
    pass

from traceback import format_list, extract_stack

# minimal IP:Port regexp
NODE_RE = re.compile('^\d+\.\d+\.\d+\.\d+:\d+$')

# Using a RAM property (not a property of an instance) allows
# to prevent from storing a state in the ZODB (and allows to restart...)
active_threads = 0
max_active_threads = 1 # 2 will cause more bug to appear (he he)
is_initialized = False
tic_lock = threading.Lock() # A RAM based lock to prevent too many concurrent tic() calls
timerservice_lock = threading.Lock() # A RAM based lock to prevent TimerService spamming when busy
is_running_lock = threading.Lock()
currentNode = None
ROLE_IDLE = 0
ROLE_PROCESSING = 1

# Activity Registration
activity_dict = {}

# Logging channel definitions
import logging
# Main logging channel
activity_logger = logging.getLogger('CMFActivity')
# Some logging subchannels
activity_tracking_logger = logging.getLogger('Tracking')
activity_timing_logger = logging.getLogger('CMFActivity.TimingLog')

# Direct logging to "[instancehome]/log/CMFActivity.log", if this directory exists.
# Otherwise, it will end up in root logging facility (ie, event.log).
from App.config import getConfiguration
import os
instancehome = getConfiguration().instancehome
if instancehome is not None:
  log_directory = os.path.join(instancehome, 'log')
  if os.path.isdir(log_directory):
    from Signals import Signals
    from ZConfig.components.logger.loghandler import FileHandler
    log_file_handler = FileHandler(os.path.join(log_directory, 'CMFActivity.log'))
    # Default zope log format string borrowed from
    # ZConfig/components/logger/factory.xml, but without the extra "------"
    # line separating entries.
    log_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%dT%H:%M:%S"))
    Signals.registerZopeSignals([log_file_handler])
    activity_logger.addHandler(log_file_handler)
    activity_logger.propagate = 0

def activity_timing_method(method, args, kw):
  begin = time()
  try:
    return method(*args, **kw)
  finally:
    end = time()
    activity_timing_logger.info('%.02fs: %r(*%r, **%r)' % (end - begin, method, args, kw))

# Here go ActivityBuffer instances
# Structure:
#  global_activity_buffer[activity_tool_path][thread_id] = ActivityBuffer
global_activity_buffer = {}
from thread import get_ident, allocate_lock
global_activity_buffer_lock = allocate_lock()

def registerActivity(activity):
  # Must be rewritten to register
  # class and create instance for each activity
  #LOG('Init Activity', 0, str(activity.__name__))
  activity_instance = activity()
  activity_dict[activity.__name__] = activity_instance

MESSAGE_NOT_EXECUTED = 0
MESSAGE_EXECUTED = 1
MESSAGE_NOT_EXECUTABLE = 2


class Message(BaseMessage):
  """Activity Message Class.

  Message instances are stored in an activity queue, inside the Activity Tool.
  """

  active_process = None
  active_process_uid = None
  call_traceback = None
  exc_info = None
  is_executed = MESSAGE_NOT_EXECUTED
  processing = None
  traceback = None
  oid = None

  def __init__(self, obj, active_process, activity_kw, method_id, args, kw):
    if isinstance(obj, str):
      self.object_path = tuple(obj.split('/'))
      activity_creation_trace = False
    else:
      self.object_path = obj.getPhysicalPath()
      activity_creation_trace = obj.getPortalObject().portal_activities.activity_creation_trace
      try:
        self.oid = aq_base(obj)._p_oid
        # Note that it's too early to get the OID of a newly created object,
        # so at this point, self.oid may still be None.
      except AttributeError:
        pass
    if active_process is not None:
      self.active_process = active_process.getPhysicalPath()
      self.active_process_uid = active_process.getUid()
    if activity_kw.get('serialization_tag', False) is None:
      # Remove serialization_tag if it's None.
      del activity_kw['serialization_tag']
    self.activity_kw = activity_kw
    self.method_id = method_id
    self.args = args
    self.kw = kw
    if activity_creation_trace and format_list is not None:
      # Save current traceback, to make it possible to tell where a message
      # was generated.
      # Strip last stack entry, since it will always be the same.
      self.call_traceback = ''.join(format_list(extract_stack()[:-1]))
    self.user_name = str(_getAuthenticatedUser(self))
    # Store REQUEST Info
    self.request_info = {}
    request = getattr(obj, 'REQUEST', None)
    if request is not None:
      if 'SERVER_URL' in request.other:
        self.request_info['SERVER_URL'] = request.other['SERVER_URL']
      if 'VirtualRootPhysicalPath' in request.other:
        self.request_info['VirtualRootPhysicalPath'] = \
          request.other['VirtualRootPhysicalPath']
      if 'HTTP_ACCEPT_LANGUAGE' in request.environ:
        self.request_info['HTTP_ACCEPT_LANGUAGE'] = \
          request.environ['HTTP_ACCEPT_LANGUAGE']
      self.request_info['_script'] = list(request._script)

  @staticmethod
  def load(s, **kw):
    self = loads(s)
    self.__dict__.update(kw)
    return self

  dump = dumps

  def getGroupId(self):
    get = self.activity_kw.get
    group_method_id = get('group_method_id', '')
    if group_method_id is None:
      group_method_id = 'portal_activities/dummyGroupMethod/' + self.method_id
    return group_method_id + '\0' + get('group_id', '')

  def getObject(self, activity_tool):
    """return the object referenced in this message."""
    try:
      obj = activity_tool.unrestrictedTraverse(self.object_path)
    except KeyError:
      LOG('CMFActivity', WARNING, "Message dropped (no object found at path %r)"
          % (self.object_path,), error=sys.exc_info())
      self.setExecutionState(MESSAGE_NOT_EXECUTABLE)
    else:
      if self.oid and self.oid != getattr(aq_base(obj), '_p_oid', None):
        raise ValueError("OID mismatch for %r" % obj)
      return obj

  def getObjectList(self, activity_tool):
    """return the list of object that can be expanded from this message
    An expand method is used to expand the list of objects and to turn a
    big recursive transaction affecting many objects into multiple
    transactions affecting only one object at a time (this can prevent
    duplicated method calls)."""
    obj = self.getObject(activity_tool)
    if obj is None:
      return ()
    if 'expand_method_id' in self.activity_kw:
      return getattr(obj, self.activity_kw['expand_method_id'])()
    return obj,

  def getObjectCount(self, activity_tool):
    if 'expand_method_id' in self.activity_kw:
      try:
        obj = activity_tool.unrestrictedTraverse(self.object_path)
        return len(getattr(obj, self.activity_kw['expand_method_id'])())
      except StandardError:
        pass
    return 1

  def changeUser(self, user_name, activity_tool):
    """restore the security context for the calling user."""
    portal = activity_tool.getPortalObject()
    portal_uf = portal.acl_users
    uf = portal_uf
    user = uf.getUserById(user_name)
    # if the user is not found, try to get it from a parent acl_users
    # XXX this is still far from perfect, because we need to store all
    # information about the user (like original user folder, roles) to
    # replay the activity with exactly the same security context as if
    # it had been executed without activity.
    if user is None:
      uf = portal.aq_parent.acl_users
      user = uf.getUserById(user_name)
    if user is not None:
      user = user.__of__(uf)
      newSecurityManager(None, user)
    else :
      LOG("CMFActivity", WARNING,
          "Unable to find user %r in the portal" % user_name)
      noSecurityManager()
    return user

  def activateResult(self, active_process, result, object):
    if not isinstance(result, ActiveResult):
      result = ActiveResult(result=result)
    # XXX Allow other method_id in future
    result.edit(object_path=object, method_id=self.method_id)
    active_process.postResult(result)

  def __call__(self, activity_tool):
    try:
      obj = self.getObject(activity_tool)
      if obj is not None:
        old_security_manager = getSecurityManager()
        try:
          # Change user if required (TO BE DONE)
          # We will change the user only in order to execute this method
          self.changeUser(self.user_name, activity_tool)
          # XXX: There is no check to see if user is allowed to access
          #      that method !
          method = getattr(obj, self.method_id)
          # Store site info
          setSite(activity_tool.getParentValue())
          if activity_tool.activity_timing_log:
            result = activity_timing_method(method, self.args, self.kw)
          else:
            result = method(*self.args, **self.kw)
        finally:
          setSecurityManager(old_security_manager)

        if method is not None:
          if self.active_process and result is not None:
            self.activateResult(
              activity_tool.unrestrictedTraverse(self.active_process),
              result, obj)
          self.setExecutionState(MESSAGE_EXECUTED)
    except:
      self.setExecutionState(MESSAGE_NOT_EXECUTED, context=activity_tool)

  def validate(self, activity, activity_tool, check_order_validation=1):
    return activity.validate(activity_tool, self,
                             check_order_validation=check_order_validation,
                             **self.activity_kw)

  def notifyUser(self, activity_tool, retry=False):
    """Notify the user that the activity failed."""
    portal = activity_tool.getPortalObject()
    user_email = portal.getProperty('email_to_address',
                       portal.getProperty('email_from_address'))
    email_from_name = portal.getProperty('email_from_name',
                       portal.getProperty('email_from_address'))
    fail_count = self.line.retry + 1
    if retry:
      message = "Pending activity already failed %s times" % fail_count
    else:
      message = "Activity failed"
    path = '/'.join(self.object_path)
    mail_text = """From: %s <%s>
To: %s
Subject: %s: %s/%s

Node: %s
Failures: %s
User name: %r
Document: %s
Method: %s
Arguments: %r
Named Parameters: %r
""" % (email_from_name, activity_tool.email_from_address, user_email, message,
       path, self.method_id, activity_tool.getCurrentNode(), fail_count,
       self.user_name, path, self.method_id, self.args, self.kw)
    if self.traceback:
      mail_text += '\nException:\n' + self.traceback
    if self.call_traceback:
      mail_text += '\nCreated at:\n' + self.call_traceback
    try:
      portal.MailHost.send(mail_text)
    except (socket.error, MailHostError), message:
      LOG('ActivityTool.notifyUser', WARNING,
          'Mail containing failure information failed to be sent: %s' % message)

  def reactivate(self, activity_tool, activity=DEFAULT_ACTIVITY):
    # Reactivate the original object.
    obj = activity_tool.unrestrictedTraverse(self.object_path)
    old_security_manager = getSecurityManager()
    try:
      # Change user if required (TO BE DONE)
      # We will change the user only in order to execute this method
      user = self.changeUser(self.user_name, activity_tool)
      active_obj = obj.activate(activity=activity, **self.activity_kw)
      getattr(active_obj, self.method_id)(*self.args, **self.kw)
    finally:
      # Use again the previous user
      setSecurityManager(old_security_manager)

  def setExecutionState(self, is_executed, exc_info=None, log=True, context=None):
    """
      Set message execution state.

      is_executed can be one of MESSAGE_NOT_EXECUTED, MESSAGE_EXECUTED and
      MESSAGE_NOT_EXECUTABLE (variables defined above).
      
      exc_info must be - if given - similar to sys.exc_info() return value.

      log must be - if given - True or False. If True, a log line will be
      emited with failure details. This parameter should only be used when
      invoking this method on a list of messages to avoid log flood. It is
      caller's responsability to output a log line summing up all errors, and
      to store error in Zope's error_log.

      context must be - if given - an object wrapped in acquisition context.
      It is used to access Zope's error_log object. It is not used if log is
      False.

      If given state is not MESSAGE_EXECUTED, it will also store given
      exc_info. If not given, it will extract one using sys.exc_info().
      If final exc_info does not contain any exception, current stack trace
      will be stored instead: it will hopefuly help understand why message
      is in an error state.
    """
    assert is_executed in (MESSAGE_NOT_EXECUTED, MESSAGE_EXECUTED, MESSAGE_NOT_EXECUTABLE)
    self.is_executed = is_executed
    if is_executed == MESSAGE_NOT_EXECUTED:
      if not exc_info:
        exc_info = sys.exc_info()
      if self.on_error_callback is not None:
        self.exc_info = exc_info
      self.exc_type = exc_info[0]
      if exc_info[0] is None:
        # Raise a dummy exception, ignore it, fetch it and use it as if it was the error causing message non-execution. This will help identifyting the cause of this misbehaviour.
        try:
          raise Exception, 'Message execution failed, but there is no exception to explain it. This is a dummy exception so that one can track down why we end up here outside of an exception handling code path.'
        except Exception:
          exc_info = sys.exc_info()
      if log:
        LOG('ActivityTool', WARNING, 'Could not call method %s on object %s. Activity created at:\n%s' % (self.method_id, self.object_path, self.call_traceback), error=exc_info)
        # push the error in ZODB error_log
        error_log = getattr(context, 'error_log', None)
        if error_log is not None:
          error_log.raising(exc_info)
      self.traceback = ''.join(ExceptionFormatter.format_exception(*exc_info)[1:])

  def getExecutionState(self):
    return self.is_executed

class Method:

  def __init__(self, passive_self, activity, active_process, kw, method_id):
    self.__passive_self = passive_self
    self.__activity = activity
    self.__active_process = active_process
    self.__kw = kw
    self.__method_id = method_id

  def __call__(self, *args, **kw):
    passive_self = self.__passive_self
    m = Message(passive_self, self.__active_process, self.__kw, self.__method_id, args, kw)
    portal_activities = passive_self.getPortalObject().portal_activities
    if portal_activities.activity_tracking:
      activity_tracking_logger.info('queuing message: activity=%s, object_path=%s, method_id=%s, args=%s, kw=%s, activity_kw=%s, user_name=%s' % (self.__activity, '/'.join(m.object_path), m.method_id, m.args, m.kw, m.activity_kw, m.user_name))
    portal_activities.getActivityBuffer().deferredQueueMessage(
      portal_activities, activity_dict[self.__activity], m)

allow_class(Method)

class ActiveWrapper:
  # XXX: maybe we should accept and forward an 'activity_tool' parameter,
  #      so that Method:
  #      - does not need to search it again
  #      - a string can be passed as first parameter to ActiveWrapper

  def __init__(self, passive_self, activity, active_process, kw):
    self.__dict__['__passive_self'] = passive_self
    self.__dict__['__activity'] = activity
    self.__dict__['__active_process'] = active_process
    self.__dict__['__kw'] = kw

  def __getattr__(self, id):
    return Method(self.__dict__['__passive_self'], self.__dict__['__activity'],
                  self.__dict__['__active_process'],
                  self.__dict__['__kw'], id)

  def __repr__(self):
    return '<%s at 0x%x to %r>' % (self.__class__.__name__, id(self),
                                   self.__dict__['__passive_self'])

# True when activities cannot be executing any more.
has_processed_shutdown = False

def cancelProcessShutdown():
  """
    This method reverts the effect of calling "process_shutdown" on activity
    tool.
  """
  global has_processed_shutdown
  is_running_lock.release()
  has_processed_shutdown = False

class ActivityTool (Folder, UniqueObject):
    """
    ActivityTool is the central point for activity management.

    Improvement to consider to reduce locks:

      Idea 1: create an SQL tool which accumulate queries and executes them at the end of a transaction,
              thus allowing all SQL transaction to happen in a very short time
              (this would also be a great way of using MyISAM tables)

      Idea 2: do the same at the level of ActivityTool

      Idea 3: do the same at the level of each activity (ie. queueMessage
              accumulates and fires messages at the end of the transactino)
    """
    id = 'portal_activities'
    meta_type = 'CMF Activity Tool'
    portal_type = 'Activity Tool'
    allowed_types = ( 'CMF Active Process', )
    security = ClassSecurityInfo()

    isIndexable = False

    manage_options = tuple(
                     [ { 'label' : 'Overview', 'action' : 'manage_overview' }
                     , { 'label' : 'Activities', 'action' : 'manageActivities' }
                     , { 'label' : 'LoadBalancing', 'action' : 'manageLoadBalancing'}
                     , { 'label' : 'Advanced', 'action' : 'manageActivitiesAdvanced' }
                     ,
                     ] + list(Folder.manage_options))

    security.declareProtected( CMFCorePermissions.ManagePortal , 'manageActivities' )
    manageActivities = DTMLFile( 'dtml/manageActivities', globals() )

    security.declareProtected( CMFCorePermissions.ManagePortal , 'manageActivitiesAdvanced' )
    manageActivitiesAdvanced = DTMLFile( 'dtml/manageActivitiesAdvanced', globals() )

    security.declareProtected( CMFCorePermissions.ManagePortal , 'manage_overview' )
    manage_overview = DTMLFile( 'dtml/explainActivityTool', globals() )
    
    security.declareProtected( CMFCorePermissions.ManagePortal , 'manageLoadBalancing' )
    manageLoadBalancing = DTMLFile( 'dtml/manageLoadBalancing', globals() )
    
    distributingNode = ''
    _nodes = ()
    activity_creation_trace = False
    activity_tracking = False
    activity_timing_log = False
    cancel_and_invoke_links_hidden = False

    def SQLDict_setPriority(self, **kw):
      real_SQLDict_setPriority = getattr(self.aq_parent, 'SQLDict_setPriority')
      LOG('ActivityTool', 0, real_SQLDict_setPriority(src__=1, **kw))
      return real_SQLDict_setPriority(**kw)

    def __init__(self, id=None):
        if id is None:
          id = ActivityTool.id
        return Folder.__init__(self, id)

    # Filter content (ZMI))
    def filtered_meta_types(self, user=None):
        # Filters the list of available meta types.
        all = Folder.filtered_meta_types(self)
        meta_types = []
        for meta_type in self.all_meta_types():
            if meta_type['name'] in self.allowed_types:
                meta_types.append(meta_type)
        return meta_types

    def maybeMigrateConnectionClass(self):
      connection_id = 'cmf_activity_sql_connection'
      sql_connection = getattr(self, connection_id, None)
      if (sql_connection is not None and
          not isinstance(sql_connection, ActivityConnection)):
        # SQL Connection migration is needed
        LOG('ActivityTool', WARNING, "Migrating MySQL Connection class")
        parent = aq_parent(aq_inner(sql_connection))
        parent._delObject(sql_connection.getId())
        new_sql_connection = ActivityConnection(connection_id,
                                                sql_connection.title,
                                                sql_connection.connection_string)
        parent._setObject(connection_id, new_sql_connection)

    def initialize(self):
      global is_initialized
      from Activity import SQLQueue, SQLDict
      # Initialize each queue
      for activity in activity_dict.itervalues():
        activity.initialize(self)
      self.maybeMigrateConnectionClass()
      is_initialized = True

    security.declareProtected(Permissions.manage_properties, 'isSubscribed')
    def isSubscribed(self):
        """
        return True, if we are subscribed to TimerService.
        Otherwise return False.
        """
        service = getTimerService(self)
        if not service:
            LOG('ActivityTool', INFO, 'TimerService not available')
            return False
        
        path = '/'.join(self.getPhysicalPath())
        if path in service.lisSubscriptions():
            return True
        return False

    security.declareProtected(Permissions.manage_properties, 'subscribe')
    def subscribe(self, REQUEST=None, RESPONSE=None):
        """ subscribe to the global Timer Service """
        service = getTimerService(self)
        url = '%s/manageLoadBalancing?manage_tabs_message=' %self.absolute_url()
        if not service:
            LOG('ActivityTool', INFO, 'TimerService not available')
            url += urllib.quote('TimerService not available')
        else:
            service.subscribe(self)
            url += urllib.quote("Subscribed to Timer Service")
        if RESPONSE is not None:
            RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'unsubscribe')
    def unsubscribe(self, REQUEST=None, RESPONSE=None):
        """ unsubscribe from the global Timer Service """
        service = getTimerService(self)
        url = '%s/manageLoadBalancing?manage_tabs_message=' %self.absolute_url()
        if not service:
            LOG('ActivityTool', INFO, 'TimerService not available')
            url += urllib.quote('TimerService not available')
        else:
            service.unsubscribe(self)
            url += urllib.quote("Unsubscribed from Timer Service")
        if RESPONSE is not None:
            RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'isActivityTrackingEnabled')
    def isActivityTrackingEnabled(self):
      return self.activity_tracking

    security.declareProtected(Permissions.manage_properties, 'manage_enableActivityTracking')
    def manage_enableActivityTracking(self, REQUEST=None, RESPONSE=None):
        """
          Enable activity tracing.
        """
        self.activity_tracking = True
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Tracking log enabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'manage_disableActivityTracking')
    def manage_disableActivityTracking(self, REQUEST=None, RESPONSE=None):
        """
          Disable activity tracing.
        """
        self.activity_tracking = False
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Tracking log disabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'isActivityTimingLoggingEnabled')
    def isActivityTimingLoggingEnabled(self):
      return self.activity_timing_log

    security.declareProtected(Permissions.manage_properties, 'manage_enableActivityTimingLogging')
    def manage_enableActivityTimingLogging(self, REQUEST=None, RESPONSE=None):
        """
          Enable activity timing logging.
        """
        self.activity_timing_log = True
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Timing log enabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'manage_disableActivityTimingLogging')
    def manage_disableActivityTimingLogging(self, REQUEST=None, RESPONSE=None):
        """
          Disable activity timing logging.
        """
        self.activity_timing_log = False
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Timing log disabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'isActivityCreationTraceEnabled')
    def isActivityCreationTraceEnabled(self):
      return self.activity_creation_trace

    security.declareProtected(Permissions.manage_properties, 'manage_enableActivityCreationTrace')
    def manage_enableActivityCreationTrace(self, REQUEST=None, RESPONSE=None):
        """
          Enable activity creation trace.
        """
        self.activity_creation_trace = True
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Activity creation trace enabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'manage_disableActivityCreationTrace')
    def manage_disableActivityCreationTrace(self, REQUEST=None, RESPONSE=None):
        """
          Disable activity creation trace.
        """
        self.activity_creation_trace = False
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Activity creation trace disabled')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'isCancelAndInvokeLinksHidden')
    def isCancelAndInvokeLinksHidden(self):
      return self.cancel_and_invoke_links_hidden

    security.declareProtected(Permissions.manage_properties, 'manage_hideCancelAndInvokeLinks')
    def manage_hideCancelAndInvokeLinks(self, REQUEST=None, RESPONSE=None):
        """
        """
        self.cancel_and_invoke_links_hidden = True
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Cancel and invoke links hidden')
          RESPONSE.redirect(url)

    security.declareProtected(Permissions.manage_properties, 'manage_showCancelAndInvokeLinks')
    def manage_showCancelAndInvokeLinks(self, REQUEST=None, RESPONSE=None):
        """
        """
        self.cancel_and_invoke_links_hidden = False
        if RESPONSE is not None:
          url = '%s/manageActivitiesAdvanced?manage_tabs_message=' % self.absolute_url()
          url += urllib.quote('Cancel and invoke links visible')
          RESPONSE.redirect(url)

    def manage_beforeDelete(self, item, container):
        self.unsubscribe()
        Folder.inheritedAttribute('manage_beforeDelete')(self, item, container)
    
    def manage_afterAdd(self, item, container):
        self.subscribe()
        Folder.inheritedAttribute('manage_afterAdd')(self, item, container)
       
    def getCurrentNode(self):
        """ Return current node in form ip:port """
        global currentNode
        if currentNode is None:
          ip = port = ''
          from asyncore import socket_map
          for k, v in socket_map.items():
              if hasattr(v, 'addr'):
                  # see Zope/lib/python/App/ApplicationManager.py: def getServers(self)
                  type = str(getattr(v, '__class__', 'unknown'))
                  if type == 'ZServer.HTTPServer.zhttp_server':
                      ip, port = v.addr
                      break
          if ip == '0.0.0.0':
            ip = socket.gethostbyname(socket.gethostname())
          currentNode = '%s:%s' %(ip, port)
        return currentNode
        
    security.declarePublic('getDistributingNode')
    def getDistributingNode(self):
        """ Return the distributingNode """
        return self.distributingNode

    def getNodeList(self, role=None):
      node_dict = self.getNodeDict()
      if role is None:
        result = [x for x in node_dict.keys()]
      else:
        result = [node_id for node_id, node_role in node_dict.items() if node_role == role]
      result.sort()
      return result

    def getNodeDict(self):
      nodes = self._nodes
      if isinstance(nodes, tuple):
        new_nodes = OIBTree()
        new_nodes.update([(x, ROLE_PROCESSING) for x in nodes])
        self._nodes = nodes = new_nodes
      return nodes

    def registerNode(self, node):
      node_dict = self.getNodeDict()
      if not node_dict.has_key(node):
        if len(node_dict) == 0: # If we are registering the first node, make
                                # it both the distributing node and a processing
                                # node.
          role = ROLE_PROCESSING
          self.distributingNode = node
        else:
          role = ROLE_IDLE
        self.updateNode(node, role)

    def updateNode(self, node, role):
      node_dict = self.getNodeDict()
      node_dict[node] = role

    security.declareProtected(CMFCorePermissions.ManagePortal, 'getProcessingNodeList')
    def getProcessingNodeList(self):
      return self.getNodeList(role=ROLE_PROCESSING)

    security.declareProtected(CMFCorePermissions.ManagePortal, 'getIdleNodeList')
    def getIdleNodeList(self):
      return self.getNodeList(role=ROLE_IDLE)

    def _isValidNodeName(self, node_name) :
      """Check we have been provided a good node name"""
      return isinstance(node_name, str) and NODE_RE.match(node_name)
      
    security.declarePublic('manage_setDistributingNode')
    def manage_setDistributingNode(self, distributingNode, REQUEST=None):
        """ set the distributing node """   
        if not distributingNode or self._isValidNodeName(distributingNode):
          self.distributingNode = distributingNode
          if REQUEST is not None:
              REQUEST.RESPONSE.redirect(
                  REQUEST.URL1 +
                  '/manageLoadBalancing?manage_tabs_message=' +
                  urllib.quote("Distributing Node successfully changed."))
        else :
          if REQUEST is not None:
              REQUEST.RESPONSE.redirect(
                  REQUEST.URL1 +
                  '/manageLoadBalancing?manage_tabs_message=' +
                  urllib.quote("Malformed Distributing Node."))

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_delNode')
    def manage_delNode(self, unused_node_list=None, REQUEST=None):
      """ delete selected unused nodes """
      processing_node = self.getDistributingNode()
      updated_processing_node = False
      if unused_node_list is not None:
        node_dict = self.getNodeDict()
        for node in unused_node_list:
          if node in node_dict:
            del node_dict[node]
          if node == processing_node:
            self.processing_node = ''
            updated_processing_node = True
      if REQUEST is not None:
        if unused_node_list is None:
          message = "No unused node selected, nothing deleted."
        else:
          message = "Deleted nodes %r." % (unused_node_list, )
        if updated_processing_node:
          message += "Disabled distributing node because it was deleted."
        REQUEST.RESPONSE.redirect(
          REQUEST.URL1 +
          '/manageLoadBalancing?manage_tabs_message=' +
          urllib.quote(message))

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_addToProcessingList')
    def manage_addToProcessingList(self, unused_node_list=None, REQUEST=None):
      """ Change one or more idle nodes into processing nodes """
      if unused_node_list is not None:
        for node in unused_node_list:
          self.updateNode(node, ROLE_PROCESSING)
      if REQUEST is not None:
        if unused_node_list is None:
          message = "No unused node selected, nothing done."
        else:
          message = "Nodes now procesing: %r." % (unused_node_list, )
        REQUEST.RESPONSE.redirect(
          REQUEST.URL1 +
          '/manageLoadBalancing?manage_tabs_message=' +
          urllib.quote(message))

    security.declareProtected(CMFCorePermissions.ManagePortal, 'manage_removeFromProcessingList')
    def manage_removeFromProcessingList(self, processing_node_list=None, REQUEST=None):
      """ Change one or more procesing nodes into idle nodes """
      if processing_node_list is not None:
        for node in processing_node_list:
          self.updateNode(node, ROLE_IDLE)
      if REQUEST is not None:
        if processing_node_list is None:
          message = "No used node selected, nothing done."
        else:
          message = "Nodes now unused %r." % (processing_node_list, )
        REQUEST.RESPONSE.redirect(
          REQUEST.URL1 +
          '/manageLoadBalancing?manage_tabs_message=' +
          urllib.quote(message))

    def process_shutdown(self, phase, time_in_phase):
        """
          Prevent shutdown from happening while an activity queue is
          processing a batch.
        """
        global has_processed_shutdown
        if phase == 3 and not has_processed_shutdown:
          has_processed_shutdown = True
          LOG('CMFActivity', INFO, "Shutdown: Waiting for activities to finish.")
          is_running_lock.acquire()
          LOG('CMFActivity', INFO, "Shutdown: Activities finished.")

    def process_timer(self, tick, interval, prev="", next=""):
      """
      Call distribute() if we are the Distributing Node and call tic()
      with our node number.
      This method is called by TimerService in the interval given
      in zope.conf. The Default is every 5 seconds.
      """
      # Prevent TimerService from starting multiple threads in parallel
      if timerservice_lock.acquire(0):
        try:
          # make sure our skin is set-up. On CMF 1.5 it's setup by acquisition,
          # but on 2.2 it's by traversal, and our site probably wasn't traversed
          # by the timerserver request, which goes into the Zope Control_Panel
          # calling it a second time is a harmless and cheap no-op.
          # both setupCurrentSkin and REQUEST are acquired from containers.
          self.setupCurrentSkin(self.REQUEST)
          old_sm = getSecurityManager()
          try:
            # get owner of portal_catalog, so normally we should be able to
            # have the permission to invoke all activities
            user = self.portal_catalog.getWrappedOwner()
            newSecurityManager(self.REQUEST, user)

            currentNode = self.getCurrentNode()
            self.registerNode(currentNode)
            processing_node_list = self.getNodeList(role=ROLE_PROCESSING)

            # only distribute when we are the distributingNode
            if self.getDistributingNode() == currentNode:
              self.distribute(len(processing_node_list))

            # SkinsTool uses a REQUEST cache to store skin objects, as
            # with TimerService we have the same REQUEST over multiple
            # portals, we clear this cache to make sure the cache doesn't
            # contains skins from another portal.
            try:
              self.getPortalObject().portal_skins.changeSkin(None)
            except AttributeError:
              pass

            # call tic for the current processing_node
            # the processing_node numbers are the indices of the elements
            # in the node tuple +1 because processing_node starts form 1
            if currentNode in processing_node_list:
              self.tic(processing_node_list.index(currentNode) + 1)
          except:
            # Catch ALL exception to avoid killing timerserver.
            LOG('ActivityTool', ERROR, 'process_timer received an exception',
                error=sys.exc_info())
          finally:
            setSecurityManager(old_sm)
        finally:
          timerservice_lock.release()

    security.declarePublic('distribute')
    def distribute(self, node_count=1):
      """
        Distribute load
      """
      # Initialize if needed
      if not is_initialized:
        self.initialize()

      # Call distribute on each queue
      for activity in activity_dict.itervalues():
        activity.distribute(aq_inner(self), node_count)

    security.declarePublic('tic')
    def tic(self, processing_node=1, force=0):
      """
        Starts again an activity
        processing_node starts from 1 (there is not node 0)
      """
      global active_threads

      # return if the number of threads is too high
      # else, increase the number of active_threads and continue
      tic_lock.acquire()
      too_many_threads = (active_threads >= max_active_threads)
      if not too_many_threads or force:
        active_threads += 1
      else:
        tic_lock.release()
        raise RuntimeError, 'Too many threads'
      tic_lock.release()

      # Initialize if needed
      if not is_initialized:
        self.initialize()

      inner_self = aq_inner(self)

      try:
        # Loop as long as there are activities. Always process the queue with
        # "highest" priority. If several queues have same highest priority, do
        # not choose one that has just been processed.
        # This algorithm is fair enough because we only have 2 queues.
        # Otherwise, a round-robin of highest-priority queues would be required.
        # XXX: We always finish by iterating over all queues, in case that
        #      getPriority does not see messages dequeueMessage would process.
        last = None
        def sort_key(activity):
          return activity.getPriority(self), activity is last
        while is_running_lock.acquire(0):
          try:
            for last in sorted(activity_dict.values(), key=sort_key):
              # Transaction processing is the responsability of the activity
              if not last.dequeueMessage(inner_self, processing_node):
                break
            else:
              break
          finally:
            is_running_lock.release()
      finally:
        # decrease the number of active_threads
        tic_lock.acquire()
        active_threads -= 1
        tic_lock.release()

    def hasActivity(self, *args, **kw):
      # Check in each queue if the object has deferred tasks
      # if not argument is provided, then check on self
      if len(args) > 0:
        obj = args[0]
      else:
        obj = self
      for activity in activity_dict.itervalues():
        if activity.hasActivity(aq_inner(self), obj, **kw):
          return True
      return False

    def getActivityBuffer(self, create_if_not_found=True):
      """
        Get activtity buffer for this thread for this activity tool.
        If no activity buffer is found at lowest level and create_if_not_found
        is True, create one.
        Intermediate level is unconditionaly created if non existant because
        chances are it will be used in the instance life.
        Lock is held when checking for intermediate level existance
        because:
         - intermediate level dict must not be created in 2 threads at the
           same time, since one creation would destroy the existing one.
        It's released after that step because:
         - lower level access is at thread scope, thus by definition there
           can be only one access at a time to a key
         - GIL protects us when accessing python instances
      """
      # Safeguard: make sure we are wrapped in  acquisition context before
      # using our path as an activity tool instance-wide identifier.
      assert getattr(self, 'aq_self', None) is not None
      my_instance_key = self.getPhysicalPath()
      my_thread_key = get_ident()
      global_activity_buffer_lock.acquire()
      try:
        if my_instance_key not in global_activity_buffer:
          global_activity_buffer[my_instance_key] = {}
      finally:
        global_activity_buffer_lock.release()
      thread_activity_buffer = global_activity_buffer[my_instance_key]
      try:
        return thread_activity_buffer[my_thread_key]
      except KeyError:
        if create_if_not_found:
          buffer = ActivityBuffer()
        else:
          buffer = None
        thread_activity_buffer[my_thread_key] = buffer
        return buffer

    security.declarePrivate('activateObject')
    def activateObject(self, object, activity, active_process, **kw):
      if not is_initialized:
        self.initialize()
      self.getActivityBuffer()
      if isinstance(active_process, str):
        active_process = self.unrestrictedTraverse(active_process)
      return ActiveWrapper(object, activity, active_process, kw)

    def getRegisteredMessageList(self, activity):
      activity_buffer = self.getActivityBuffer(create_if_not_found=False)
      if activity_buffer is not None:
        #activity_buffer._register() # This is required if flush flush is called outside activate
        return activity.getRegisteredMessageList(activity_buffer,
                                                 aq_inner(self))
      else:
        return []

    def unregisterMessage(self, activity, message):
      activity_buffer = self.getActivityBuffer()
      #activity_buffer._register()
      return activity.unregisterMessage(activity_buffer, aq_inner(self), message)

    def flush(self, obj, invoke=0, **kw):
      if not is_initialized:
        self.initialize()
      self.getActivityBuffer()
      if isinstance(obj, tuple):
        object_path = obj
      else:
        object_path = obj.getPhysicalPath()
      for activity in activity_dict.itervalues():
        activity.flush(aq_inner(self), object_path, invoke=invoke, **kw)

    def invoke(self, message):
      if self.activity_tracking:
        activity_tracking_logger.info('invoking message: object_path=%s, method_id=%s, args=%r, kw=%r, activity_kw=%r, user_name=%s' % ('/'.join(message.object_path), message.method_id, message.args, message.kw, message.activity_kw, message.user_name))
      old_localizer_context = False
      if getattr(self, 'aq_chain', None) is not None:
        # Grab existing acquisition chain and extrach base objects.
        base_chain = [aq_base(x) for x in self.aq_chain]
        # Grab existig request (last chain item) and create a copy.
        request_container = base_chain.pop()
        request = request_container.REQUEST
        # Generate PARENTS value. Sadly, we cannot reuse base_chain since
        # PARENTS items must be wrapped in acquisition
        parents = []
        application = self.getPhysicalRoot().aq_base
        for parent in self.aq_chain:
          if parent.aq_base is application:
            break
          parents.append(parent)
        # XXX: REQUEST.clone() requires PARENTS to be set, and it's not when
        # runing unit tests. Recreate it if it does not exist.
        if getattr(request.other, 'PARENTS', None) is None:
          request.other['PARENTS'] = parents
        # XXX: PATH_INFO might not be set when runing unit tests.
        if request.environ.get('PATH_INFO') is None:
          request.environ['PATH_INFO'] = '/Control_Panel/timer_service/process_timer'
        
        # restore request information
        new_request = request.clone()
        request_info = message.request_info
        # PARENTS is truncated by clone
        new_request.other['PARENTS'] = parents
        if '_script' in request_info:
          new_request._script = request_info['_script']
        if 'SERVER_URL' in request_info:
          new_request.other['SERVER_URL'] = request_info['SERVER_URL']
        if 'VirtualRootPhysicalPath' in request_info:
          new_request.other['VirtualRootPhysicalPath'] = request_info['VirtualRootPhysicalPath']
        if 'HTTP_ACCEPT_LANGUAGE' in request_info:
          new_request.environ['HTTP_ACCEPT_LANGUAGE'] = request_info['HTTP_ACCEPT_LANGUAGE']
          # Replace Localizer/iHotfix Context, saving existing one
          localizer_context = LocalizerContext(new_request)
          id = get_ident()
          localizer_lock.acquire()
          try:
            old_localizer_context = localizer_contexts.get(id)
            localizer_contexts[id] = localizer_context
          finally:
            localizer_lock.release()
          # Execute Localizer/iHotfix "patch 2"
          new_request.processInputs()

        new_request_container = request_container.__class__(REQUEST=new_request)
        # Recreate acquisition chain.
        my_self = new_request_container
        base_chain.reverse()
        for item in base_chain:
          my_self = item.__of__(my_self)
      else:
        my_self = self
        LOG('CMFActivity.ActivityTool.invoke', INFO, 'Strange: invoke is called outside of acquisition context.')
      try:
        message(my_self)
      finally:
        if my_self is not self: # We rewrapped self
          # Restore default skin selection
          skinnable = self.getPortalObject()
          skinnable.changeSkin(skinnable.getSkinNameFromRequest(request))
        if old_localizer_context is not False:
          # Restore Localizer/iHotfix context
          id = get_ident()
          localizer_lock.acquire()
          try:
            if old_localizer_context is None:
              del localizer_contexts[id]
            else:
              localizer_contexts[id] = old_localizer_context
          finally:
            localizer_lock.release()
      if self.activity_tracking:
        activity_tracking_logger.info('invoked message')
      if my_self is not self: # We rewrapped self
        for held in my_self.REQUEST._held:
          self.REQUEST._hold(held)

    def invokeGroup(self, method_id, message_list, activity, merge_duplicate):
      if self.activity_tracking:
        activity_tracking_logger.info(
          'invoking group messages: method_id=%s, paths=%s'
          % (method_id, ['/'.join(m.object_path) for m in message_list]))
      # Invoke a group method.
      message_dict = {}
      path_set = set()
      # Filter the list of messages. If an object is not available, mark its
      # message as non-executable. In addition, expand an object if necessary,
      # and make sure that no duplication happens.
      for m in message_list:
        # alternate method is used to segregate objects which cannot be grouped.
        alternate_method_id = m.activity_kw.get('alternate_method_id')
        try:
          object_list = m.getObjectList(self)
          if object_list is None:
            continue
          message_dict[m] = expanded_object_list = []
          for subobj in object_list:
            if merge_duplicate:
              path = subobj.getPath()
              if path in path_set:
                continue
              path_set.add(path)
            if alternate_method_id is not None \
               and hasattr(aq_base(subobj), alternate_method_id):
              # if this object is alternated,
              # generate a new single active object
              activity_kw = m.activity_kw.copy()
              activity_kw.pop('group_method_id', None)
              activity_kw.pop('group_id', None)
              active_obj = subobj.activate(activity=activity, **activity_kw)
              getattr(active_obj, alternate_method_id)(*m.args, **m.kw)
            else:
              expanded_object_list.append([subobj, m.args, m.kw, None])
        except:
          m.setExecutionState(MESSAGE_NOT_EXECUTED, context=self)

      expanded_object_list = sum(message_dict.itervalues(), [])
      try:
        if len(expanded_object_list) > 0:
          traverse = self.getPortalObject().unrestrictedTraverse
          # FIXME: how to apply security here?
          # NOTE: expanded_object_list[*][3] must be updated by the callee:
          #       it must be deleted in case of failure, or updated with the
          #       result to post on the active process otherwise.
          traverse(method_id)(expanded_object_list)
      except:
        # In this case, the group method completely failed.
        exc_info = sys.exc_info()
        for m in message_dict:
          m.setExecutionState(MESSAGE_NOT_EXECUTED, exc_info, log=False)
        LOG('WARNING ActivityTool', 0,
            'Could not call method %s on objects %s' %
            (method_id, [x[0] for x in expanded_object_list]), error=exc_info)
        error_log = getattr(self, 'error_log', None)
        if error_log is not None:
          error_log.raising(exc_info)
      else:
        # Note there can be partial failures.
        for m, expanded_object_list in message_dict.iteritems():
          result_list = []
          for result in expanded_object_list:
            if len(result) != 4:
              break # message marked as failed by the group_method_id
            elif result[3] is not None:
              result_list.append(result)
          else:
            try:
              if result_list and m.active_process:
                active_process = traverse(m.active_process)
                for result in result_list:
                  m.activateResult(active_process, result[3], result[0])
            except:
              pass
            else:
              m.setExecutionState(MESSAGE_EXECUTED, context=self)
              continue
          m.setExecutionState(MESSAGE_NOT_EXECUTED, context=self)
      if self.activity_tracking:
        activity_tracking_logger.info('invoked group messages')

    security.declarePrivate('dummyGroupMethod')
    class dummyGroupMethod(object):
      def __bobo_traverse__(self, REQUEST, method_id):
        def group_method(message_list):
          for m in message_list:
            m[3] = getattr(m[0], method_id)(*m[1], **m[2])
        return group_method
    dummyGroupMethod = dummyGroupMethod()

    def newMessage(self, activity, path, active_process,
                   activity_kw, method_id, *args, **kw):
      # Some Security Cheking should be made here XXX
      if not is_initialized:
        self.initialize()
      self.getActivityBuffer()
      activity_dict[activity].queueMessage(aq_inner(self),
        Message(path, active_process, activity_kw, method_id, args, kw))

    security.declareProtected( CMFCorePermissions.ManagePortal, 'manageInvoke' )
    def manageInvoke(self, object_path, method_id, REQUEST=None):
      """
        Invokes all methods for object "object_path"
      """
      if type(object_path) is type(''):
        object_path = tuple(object_path.split('/'))
      self.flush(object_path,method_id=method_id,invoke=1)
      if REQUEST is not None:
        return REQUEST.RESPONSE.redirect('%s/%s' %
                (self.absolute_url(), 'manageActivities'))

    security.declareProtected( CMFCorePermissions.ManagePortal, 'manageRestart')
    def manageRestart(self, message_uid_list, activity, REQUEST=None):
      """
        Restart one or several messages
      """
      if not(isinstance(message_uid_list, list)):
        message_uid_list = [message_uid_list]
      self.SQLBase_makeMessageListAvailable(table=activity_dict[activity].sql_table,
                              uid=message_uid_list)
      if REQUEST is not None:
        return REQUEST.RESPONSE.redirect('%s/%s' % (
          self.absolute_url(), 'view'))

    security.declareProtected( CMFCorePermissions.ManagePortal, 'manageCancel' )
    def manageCancel(self, object_path, method_id, REQUEST=None):
      """
        Cancel all methods for object "object_path"
      """
      LOG('ActivityTool', WARNING,
          '"manageCancel" method is deprecated, use "manageDelete" instead.')
      if type(object_path) is type(''):
        object_path = tuple(object_path.split('/'))
      self.flush(object_path,method_id=method_id,invoke=0)
      if REQUEST is not None:
        return REQUEST.RESPONSE.redirect('%s/%s' % (
          self.absolute_url(), 'view'))

    security.declareProtected( CMFCorePermissions.ManagePortal, 'manageDelete' )
    def manageDelete(self, message_uid_list, activity, REQUEST=None):
      """
        Delete one or several messages
      """
      if not(isinstance(message_uid_list, list)):
        message_uid_list = [message_uid_list]
      self.SQLBase_delMessage(table=activity_dict[activity].sql_table,
                              uid=message_uid_list)
      if REQUEST is not None:
        return REQUEST.RESPONSE.redirect('%s/%s' % (
          self.absolute_url(), 'view'))

    security.declareProtected( CMFCorePermissions.ManagePortal,
                               'manageClearActivities' )
    def manageClearActivities(self, keep=1, REQUEST=None):
      """
        Clear all activities and recreate tables.
      """
      folder = self.getPortalObject().portal_skins.activity

      # Obtain all pending messages.
      message_list_dict = {}
      if keep:
        for activity in activity_dict.itervalues():
          if hasattr(activity, 'dumpMessageList'):
            try:
              message_list_dict[activity.__class__.__name__] =\
                                    activity.dumpMessageList(self)
            except ConflictError:
              raise
            except:
              LOG('ActivityTool', WARNING,
                  'could not dump messages from %s' %
                  (activity,), error=sys.exc_info())

      if getattr(folder, 'SQLDict_createMessageTable', None) is not None:
        try:
          folder.SQLDict_dropMessageTable()
        except ConflictError:
          raise
        except:
          LOG('CMFActivity', WARNING,
              'could not drop the message table',
              error=sys.exc_info())
        folder.SQLDict_createMessageTable()

      if getattr(folder, 'SQLQueue_createMessageTable', None) is not None:
        try:
          folder.SQLQueue_dropMessageTable()
        except ConflictError:
          raise
        except:
          LOG('CMFActivity', WARNING,
              'could not drop the message queue table',
              error=sys.exc_info())
        folder.SQLQueue_createMessageTable()

      # Reactivate the messages.
      for activity, message_list in message_list_dict.iteritems():
        for m in message_list:
          try:
            m.reactivate(aq_inner(self), activity=activity)
          except ConflictError:
            raise
          except:
            LOG('ActivityTool', WARNING,
                'could not reactivate the message %r, %r' %
                (m.object_path, m.method_id), error=sys.exc_info())

      if REQUEST is not None:
        message = 'Activities%20Cleared'
        if keep:
          message = 'Tables%20Recreated'
        return REQUEST.RESPONSE.redirect(
            '%s/manageActivitiesAdvanced?manage_tabs_message=%s' % (
              self.absolute_url(), message))

    security.declarePublic('getMessageTempObjectList')
    def getMessageTempObjectList(self, **kw):
      """
        Get object list of messages waiting in queues
      """
      message_list = self.getMessageList(**kw)
      object_list = []
      for sql_message in message_list:
        message = self.newContent(temp_object=1)
        message.edit (**sql_message.__dict__)
        object_list.append(message)
      return object_list

    security.declarePublic('getMessageList')
    def getMessageList(self, activity=None, **kw):
      """
        List messages waiting in queues
      """
      # Initialize if needed
      if not is_initialized:
        self.initialize()
      if activity:
        return activity_dict[activity].getMessageList(aq_inner(self), **kw)

      message_list = []
      for activity in activity_dict.itervalues():
        try:
          message_list += activity.getMessageList(aq_inner(self), **kw)
        except AttributeError:
          LOG('getMessageList, could not get message from Activity:',0,activity)
      return message_list

    security.declarePublic('countMessageWithTag')
    def countMessageWithTag(self, value):
      """
        Return the number of messages which match the given tag.
      """
      message_count = 0
      for activity in activity_dict.itervalues():
        message_count += activity.countMessageWithTag(aq_inner(self), value)
      return message_count

    security.declarePublic('countMessage')
    def countMessage(self, **kw):
      """
        Return the number of messages which match the given parameter.

        Parameters allowed:

        method_id : the id of the method
        path : for activities on a particular object
        tag : activities with a particular tag
        message_uid : activities with a particular uid
      """
      message_count = 0
      for activity in activity_dict.itervalues():
        message_count += activity.countMessage(aq_inner(self), **kw)
      return message_count

    security.declareProtected( CMFCorePermissions.ManagePortal , 'newActiveProcess' )
    def newActiveProcess(self, REQUEST=None, **kw):
      # note: if one wants to create an Actice Process without ERP5 products,
      # she can call ActiveProcess.addActiveProcess
      obj = self.newContent(portal_type="Active Process", **kw)
      if REQUEST is not None:
        REQUEST['RESPONSE'].redirect( 'manage_main' )
      return obj

    # Active synchronisation methods
    security.declarePrivate('validateOrder')
    def validateOrder(self, message, validator_id, validation_value):
      message_list = self.getDependentMessageList(message, validator_id, validation_value)
      return len(message_list) > 0

    security.declarePrivate('getDependentMessageList')
    def getDependentMessageList(self, message, validator_id, validation_value):
      if not is_initialized:
        self.initialize()
      message_list = []
      method_id = "_validate_" + validator_id
      for activity in activity_dict.itervalues():
        method = getattr(activity, method_id, None)
        if method is not None:
          result = method(aq_inner(self), message, validation_value)
          if result:
            message_list += [(activity, m) for m in result]
      return message_list

    # Required for tests (time shift)
    def timeShift(self, delay):
      if not is_initialized:
        self.initialize()
      for activity in activity_dict.itervalues():
        activity.timeShift(aq_inner(self), delay)

InitializeClass(ActivityTool)
