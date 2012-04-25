taskdistribution
----------------

This library contains the API to use ERP5 Task Distribution as Client.

Basic Usage Example:

  >>> from erp5.util.taskdistribution import TaskDistributionClient
  >>> client = TaskDistributionClient("http://www.url.master.node.com/")
  >>> print client.getProtocolRevision()
  safeRpcCall called with method : getProtocolRevision
  1
  >>> client.isTaskAlive("test_result_module/20120425-725D3B5/290")
  safeRpcCall called with method : isTaskAlive
  0

Using RemoteLogger to keep updated the information on Task Distribution Module:

  1) First you need a log function

  >>> from erp5.util.log import DefaultLogger
  >>> default_log = DefaultLogger("TestLogger")
  >>> default_log.enableFileLog("/tmp/default_log")

  2) Create the Remote Logger and invoke it

  >>> logger = RemoteLogger(default_log, "/tmp/default_log", "ERP5-RAFAEL", None)
  
  3) Update with Master URL and test_path
  >>> logger.update("http://www.url.master.node.com/", "test_result_module/20120425-725D3B5")

  4) Call it, and this will handle the update of the information for you, you can use 
     thread to monitor in parallel some process group.
  >>> logger()

  
  
  
