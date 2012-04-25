import socket
import sys
import xmlrpclib
import time

from erp5.util.log import DefaultLogger

def safeRpcCall(log, proxy, function_id, retry, *args):
  # this method will try infinitive calls to backend
  # this can cause testnode to looked "stalled"
  retry_time = 64
  while True:
    try:
      # it safer to pass proxy and function_id so we avoid httplib.ResponseNotReady
      # by trying reconnect before server keep-alive ends and the socket closes
      log('safeRpcCall called with method : %s' % function_id)
      function = getattr(proxy, function_id)
      return function(*args)
    except (socket.error, xmlrpclib.ProtocolError, xmlrpclib.Fault), e:
      log('Exception in safeRpcCall when trying %s with %r' % (function_id, args),
           exc_info=sys.exc_info())
      if not(retry):
        return
      log('will retry safeRpcCall in %i seconds' % retry_time)
      time.sleep(retry_time)
      retry_time += retry_time >> 1

class TaskDistributionClient(object):

  def __init__(self, master_url, log=None):
    """
      Create one xmlrpclib connection to an ERP5 which
      contains the
    """
    assert master_url is not None
    if master_url[-1] != "/":
       master_url += '/'
    self.master_url = "%sportal_task_distribution" % master_url
    if log is None:
      log = DefaultLogger("TaskDistributionClient")
      log.enableConsole()
    self.log = log

  def __safeRpcCall(self, function_id, retry, *kw):
    """
      Invoke safeRpcCall using self.log 
    """
    master = self.__getConnection()
    return safeRpcCall(self.log, master, function_id, retry, *kw)

  def __getConnection(self):
    """
      Create one xmlrpclib connection to an ERP5 which
      contains the portal_task_distribution installed.
    """
    return xmlrpclib.ServerProxy(self.master_url, allow_none=1)

  def reportTaskFailure(self, test_result_path, status_dict, node_title, retry=False):
    """ report failure when a node can not handle task"""
    return self.__safeRpcCall("reportTaskFailure", retry, 
                test_result_path, status_dict, node_title)

  def reportTaskStatus(self, test_result_path, status_dict, node_title, retry=False):
    """ report task current status """
    return self.__safeRpcCall("reportTaskStatus", retry,
                test_result_path, status_dict, node_title)

  def createTestResult(self, name, revision, test_name_list, allow_restart,
                             test_title=None, node_title=None,
                             project_title=None, retry=False):
    """ Request the creation of a new Test Result """
    return self.__safeRpcCall("createTestResult", retry, 
                        name, revision, test_name_list, allow_restart,
                        test_title, node_title, project_title)

  def getProtocolRevision(self, retry=False):
    """ Get Protocol Revision """
    return self.__safeRpcCall("getProtocolRevision", retry)

  def startUnitTest(self, test_result_path, exclude_list=(), retry=False):
    """ Report the Unit Test Start """
    return self.__safeRpcCall("startUnitTest", retry,
                       test_result_path, exclude_list)

  def stopUnitTest(self, test_path, status_dict, retry=False):
    """ Report the Unit Test Stop """
    return self.__safeRpcCall("stopUnitTest", retry, test_path, status_dict)

  def isTaskAlive(self, test_path, retry=False):
     """ Verify if Task still alive """
     return self.__safeRpcCall("isTaskAlive", retry, test_path)

