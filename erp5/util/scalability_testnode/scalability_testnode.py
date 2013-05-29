##############################################################################
#
# Copyright (c) 2011 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
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
from datetime import datetime,timedelta
import os
import subprocess
import sys
import time
import glob
import SlapOSControler
import json
import time
import shutil
import logging
import string
import random
from ProcessManager import SubprocessError, ProcessManager, CancellationError
from subprocess import CalledProcessError
from Updater import Updater
from erp5.util import taskdistribution

import xmlrpclib

DEFAULT_SLEEP_TIMEOUT = 120 # time in seconds to sleep
MAX_LOG_TIME = 15 # time in days we should keep logs that we can see through
                  # httd
MAX_TEMP_TIME = 0.01 # time in days we should keep temp files
supervisord_pid_file = None

PROFILE_PATH_KEY = 'profile_path'

class DummyLogger(object):
  def __init__(self, func):
    for name in ('trace', 'debug', 'info', 'warn', 'warning', 'error',
      'critical', 'fatal'):
       setattr(self, name, func)

class SlapOSInstance(object):

  def __init__(self):
    self.retry_software_count = 0
    self.retry = False

  def edit(self, **kw):
    self.__dict__.update(**kw)
    self._checkData()

  def _checkData(self):
    pass

def deunicodeData(data):
  if isinstance(data, list):
    new_data = []
    for sub_data in data:
      new_data.append(deunicodeData(sub_data))
  elif isinstance(data, unicode):
    new_data = data.encode('utf8')
  elif isinstance(data, dict):
    new_data = {}
    for key, value in data.iteritems():
      key = deunicodeData(key)
      value = deunicodeData(value)
      new_data[key] = value
  return new_data

class NodeTestSuite(SlapOSInstance):

  def __init__(self, reference):
    super(NodeTestSuite, self).__init__()
    self.reference = reference

  def edit(self, **kw):
    super(NodeTestSuite, self).edit(**kw)

  def _checkData(self):
    if getattr(self, "working_directory", None) is not None:
      if not(self.working_directory.endswith(os.path.sep + self.reference)):
        self.working_directory = os.path.join(self.working_directory,
                                             self.reference)
      SlapOSControler.createFolder(self.working_directory)
      self.test_suite_directory = os.path.join(
                                   self.working_directory, "test_suite")
      self.custom_profile_path = os.path.join(self.working_directory,
                                 'software.cfg')
    if getattr(self, "vcs_repository_list", None) is not None:
      for vcs_repository in self.vcs_repository_list:
        buildout_section_id = vcs_repository.get('buildout_section_id', None)
        repository_id = buildout_section_id or \
                        vcs_repository.get('url').split('/')[-1].split('.')[0]
        repository_path = os.path.join(self.working_directory,repository_id)
        vcs_repository['repository_id'] = repository_id
        vcs_repository['repository_path'] = repository_path

  def createSuiteLog(self):
    # /srv/slapgrid/slappartXX/srv/var/log/scalability_testnode/az-mlksjfmlk234Sljssdflkj23KSdfslj/suite.log
    alphabets = string.digits + string.letters
    rand_part = ''.join(random.choice(alphabets) for i in xrange(32))
    random_suite_folder_id = '%s-%s' % (self.reference, rand_part)
    suite_log_directory = os.path.join(self.log_directory,
                                       random_suite_folder_id)
    SlapOSControler.createFolders(suite_log_directory)
    self.suite_log_path = os.path.join(suite_log_directory,
                                       'suite.log')
    return self.getSuiteLogPath(), random_suite_folder_id

  def getSuiteLogPath(self):
    return getattr(self,"suite_log_path", None)

class TestNode(object):

  def __init__(self, log, config, max_log_time=MAX_LOG_TIME,
               max_temp_time=MAX_TEMP_TIME):
    self.testnode_log = log
    self.log = log
    self.config = config or {}
    self.process_manager = ProcessManager(log)
    self.node_test_suite_dict = {}
    self.max_log_time = max_log_time
    self.max_temp_time = max_temp_time
    self.file_handler = None

  def checkOldTestSuite(self,test_suite_data):
    config = self.config
    installed_reference_set = set(os.listdir(config['working_directory']))
    wished_reference_set = set([x['test_suite_reference'] for x in test_suite_data])
    to_remove_reference_set = installed_reference_set.difference(
                                 wished_reference_set)
    for y in to_remove_reference_set:
      fpath = os.path.join(config['working_directory'],y)
      self.delNodeTestSuite(y)
      self.log("testnode.checkOldTestSuite, DELETING : %r" % (fpath,))
      if os.path.isdir(fpath):
       shutil.rmtree(fpath)
      else:
       os.remove(fpath)

  def getNodeTestSuite(self, reference):
    print "getNodeTestSuite"
    node_test_suite = self.node_test_suite_dict.get(reference)
    if node_test_suite is None:
      print "node_test_suite is None"
      node_test_suite = NodeTestSuite(reference)
      self.node_test_suite_dict[reference] = node_test_suite
    print "return:"
    print node_test_suite
    return node_test_suite

  def delNodeTestSuite(self, reference):
    if self.node_test_suite_dict.has_key(reference):
      self.node_test_suite_dict.pop(reference)

  def constructProfile(self, node_test_suite):
    config = self.config
    profile_content = ''
    assert len(node_test_suite.vcs_repository_list), "we must have at least one repository"
    profile_path_count = 0
    profile_content_list = []
    for vcs_repository in node_test_suite.vcs_repository_list:
      url = vcs_repository['url']
      buildout_section_id = vcs_repository.get('buildout_section_id', None)
      repository_path = vcs_repository['repository_path']
      try:
        profile_path = vcs_repository[PROFILE_PATH_KEY]
      except KeyError:
        pass
      else:
        profile_path_count += 1
        if profile_path_count > 1:
          raise ValueError(PROFILE_PATH_KEY + ' defined more than once')
        profile_content_list.append("""
[buildout]
extends = %(software_config_path)s
""" %  {'software_config_path': os.path.join(repository_path, profile_path)})

      if not(buildout_section_id is None):
        profile_content_list.append("""
[%(buildout_section_id)s]
repository = %(repository_path)s
branch = %(branch)s
""" %  {'buildout_section_id': buildout_section_id,
   'repository_path' : repository_path,
   'branch' : vcs_repository.get('branch','master')})
    if not profile_path_count:
      raise ValueError(PROFILE_PATH_KEY + ' not defined')
    custom_profile = open(node_test_suite.custom_profile_path, 'w')
    # sort to have buildout section first
    profile_content_list.sort(key=lambda x: [x, ''][x.startswith('\n[buildout]')])
    custom_profile.write(''.join(profile_content_list))
    custom_profile.close()
    sys.path.append(repository_path)

  def getAndUpdateFullRevisionList(self, node_test_suite):
    full_revision_list = []
    config = self.config
    log = self.log
    for vcs_repository in node_test_suite.vcs_repository_list:
      repository_path = vcs_repository['repository_path']
      repository_id = vcs_repository['repository_id']
      branch = vcs_repository.get('branch')
      if not os.path.exists(repository_path):
        parameter_list = [config['git_binary'], 'clone',
                          vcs_repository['url']]
        if branch is not None:
          parameter_list.extend(['-b', branch])
        parameter_list.append(repository_path)
        log(subprocess.check_output(parameter_list, stderr=subprocess.STDOUT))
      # Make sure we have local repository
      updater = Updater(repository_path, git_binary=config['git_binary'],
         branch=branch, log=log, process_manager=self.process_manager)
      updater.checkout()
      revision = "-".join(updater.getRevision())
      full_revision_list.append('%s=%s' % (repository_id, revision))
    node_test_suite.revision = ','.join(full_revision_list)
    return full_revision_list

  def registerSuiteLog(self, test_result, node_test_suite):
    """
      Create a log dedicated for the test suite,
      and register the url to master node.
    """
    suite_log_path, folder_id = node_test_suite.createSuiteLog()
    self._initializeSuiteLog(suite_log_path)
    # TODO make the path into url
    test_result.reportStatus('LOG url', "%s/%s" % (self.config.get('httpd_url'),
                             folder_id), '')
    self.log("going to switch to log %r" % suite_log_path)
    self.process_manager.log = self.log = self.getSuiteLog()
    return suite_log_path

  def getSuiteLog(self):
    return self.suite_log

  def _initializeSuiteLog(self, suite_log_path):
    # remove previous handlers
    logger = logging.getLogger('testsuite')
    if self.file_handler is not None:
      logger.removeHandler(self.file_handler)
    # and replace it with new handler
    logger_format = '%(asctime)s %(name)-13s: %(levelname)-8s %(message)s'
    formatter = logging.Formatter(logger_format)
    logging.basicConfig(level=logging.INFO, format=logger_format)
    self.file_handler = logging.FileHandler(filename=suite_log_path)
    self.file_handler.setFormatter(formatter)
    logger.addHandler(self.file_handler)
    logger.info('Activated logfile %r output' % suite_log_path)
    self.suite_log = logger.info

  def checkRevision(self, test_result, node_test_suite):
    config = self.config
    log = self.log
    if log is None:
      log = self.log
    if node_test_suite.revision != test_result.revision:
     log('Disagreement on tested revision, checking out: %r' % (
          (node_test_suite.revision,test_result.revision),))
     for i, repository_revision in enumerate(test_result.revision.split(',')):
      vcs_repository = node_test_suite.vcs_repository_list[i]
      repository_path = vcs_repository['repository_path']
      revision = repository_revision.rsplit('-', 1)[1]
      # other testnodes on other boxes are already ready to test another
      # revision
      log('  %s at %s' % (repository_path, node_test_suite.revision))
      updater = Updater(repository_path, git_binary=config['git_binary'],
                        revision=revision, log=log,
                        process_manager=self.process_manager)
      updater.checkout()
      node_test_suite.revision = test_result.revision

  def _dealShebang(self,run_test_suite_path):
    line = open(run_test_suite_path, 'r').readline()
    invocation_list = []
    if line[:2] == '#!':
      invocation_list = line[2:].split()
    return invocation_list

  def runTestSuite(self, node_test_suite, portal_url, log=None):
    config = self.config
    parameter_list = []
    run_test_suite_path_list = glob.glob("%s/*/bin/runTestSuite" % \
        self.slapos_controler.instance_root)
    if not len(run_test_suite_path_list):
      raise ValueError('No runTestSuite provided in installed partitions.')
    run_test_suite_path = run_test_suite_path_list[0]
    run_test_suite_revision = node_test_suite.revision
    # Deal with Shebang size limitation
    invocation_list = self._dealShebang(run_test_suite_path)
    invocation_list.extend([run_test_suite_path,
                           '--test_suite', node_test_suite.test_suite,
                           '--revision', node_test_suite.revision,
                           '--test_suite_title', node_test_suite.test_suite_title,
                           '--node_quantity', config['node_quantity'],
                           '--master_url', portal_url])
    firefox_bin_list = glob.glob("%s/soft/*/parts/firefox/firefox-slapos" % \
        config["slapos_directory"])
    if len(firefox_bin_list):
      parameter_list.append('--firefox_bin')
    xvfb_bin_list = glob.glob("%s/soft/*/parts/xserver/bin/Xvfb" % \
        config["slapos_directory"])
    if len(xvfb_bin_list):
      parameter_list.append('--xvfb_bin')
    supported_paramater_set = self.process_manager.getSupportedParameterSet(
                           run_test_suite_path, parameter_list)
    if '--firefox_bin' in supported_paramater_set:
      invocation_list.extend(["--firefox_bin", firefox_bin_list[0]])
    if '--xvfb_bin' in supported_paramater_set:
      invocation_list.extend(["--xvfb_bin", xvfb_bin_list[0]])
    bt5_path_list = config.get("bt5_path")
    if bt5_path_list not in ('', None,):
      invocation_list.extend(["--bt5_path", bt5_path_list])
    # From this point, test runner becomes responsible for updating test
    # result. We only do cleanup if the test runner itself is not able
    # to run.
    SlapOSControler.createFolder(node_test_suite.test_suite_directory,
                                 clean=True)
    self.process_manager.spawn(*invocation_list,
                          cwd=node_test_suite.test_suite_directory,
                          log_prefix='runTestSuite', get_output=False)

  def _cleanupLog(self):
    config = self.config
    log_directory = self.config['log_directory']
    now = time.time()
    for log_folder in os.listdir(log_directory):
      folder_path = os.path.join(log_directory, log_folder)
      if os.path.isdir(folder_path):
        if (now - os.stat(folder_path).st_mtime)/86400 > self.max_log_time:
          self.log("deleting log directory %r" % (folder_path,))
          shutil.rmtree(folder_path)

  def _cleanupTemporaryFiles(self):
    """
    buildout seems letting files under /tmp. To avoid regular error of
    missing disk space, remove old logs
    """
    temp_directory = self.config["system_temp_folder"]
    now = time.time()
    user_id = os.geteuid()
    for temp_folder in os.listdir(temp_directory):
      folder_path = os.path.join(temp_directory, temp_folder)
      if (temp_folder.startswith("tmp") or
          temp_folder.startswith("buildout")):
        try:
          stat = os.stat(folder_path)
          if stat.st_uid == user_id and \
              (now - stat.st_mtime)/86400 > self.max_temp_time:
            self.log("deleting temp directory %r" % (folder_path,))
            if os.path.isdir(folder_path):
              shutil.rmtree(folder_path)
            else:
              os.remove(folder_path)
        except OSError:
          self.log("_cleanupTemporaryFiles exception", exc_info=sys.exc_info())

  def cleanUp(self,test_result):
    log = self.log
    log('Testnode.cleanUp')
    self.process_manager.killPreviousRun()
    self._cleanupLog()
    self._cleanupTemporaryFiles()

  def _runAsMaster(self):
    print "I'm the master"

    self.slapos_controler = SlapOSControler.SlapOSControler(
         self.config['working_directory'], self.config, self.log)

    # how to use SlapOSControler :
    # slapos_controler._supply(config['slapos_account_slapos_cfg_path'],
    #                      'kvm.cfg', 'COMP-726')
    # slapos_controler._request(config['slapos_account_slapos_cfg_path'],
    #                      'Instance16h34Ben', 'kvm.cfg',
    #                      'cluster', { "_" : "{'toto' : 'titi'}" } ) 


    # Install (good) software
    # 1: Get the soft.cfg into the master working_directory
    # 2: configure apache to allow acces to it from outside
    # 3: install software this the ipv6 address made to access to soft.cfg
    # 4: ok?
      
    test_suite_json = self.distributor.startTestSuite(self.config['test_node_title'])
    print "test_suite_json:"
    print test_suite_json
    test_suite_data = deunicodeData(json.loads(test_suite_json))
    print "test_suite_data:"
    print test_suite_data
    self.checkOldTestSuite(test_suite_data)

    for test_suite in test_suite_data:
      print "test_suite:"
      print test_suite
      node_test_suite = self.getNodeTestSuite(test_suite["test_suite_reference"])
      node_test_suite.edit(
           working_directory=self.config['working_directory'],
           log_directory=self.config['log_directory'])
      node_test_suite.edit(**test_suite)
      # Write our own software.cfg to use the local repository
      self.constructProfile(node_test_suite)
      self.getAndUpdateFullRevisionList(node_test_suite)

      portal_task_distribution_tool = taskdistribution.TaskDistributionTool(
                                           self.portal_url,
                                           logger=DummyLogger(self.log))
#      test_result = self.distributor.createTestResult(
      test_result = portal_task_distribution_tool.createTestResult(
                       node_test_suite.revision,
                       [],
                       self.config['test_node_title'],
                       False,
                       test_suite['test_suite_title'],
                       node_test_suite.project_title)


      print "test_suite['cluster_configuration']:"
      print test_suite['cluster_configuration']
      print "test_suite['cluster_constraint']:"
      print test_suite['cluster_constraint']
      print "test_suite['number_configuration']:"
      print test_suite['number_configuration']




 
      self.registerSuiteLog(test_result, node_test_suite)
      self.checkRevision(test_result,node_test_suite)
      
      print "EndMaster"


  def _runAsSlave(self):
    print "I'm a slave"
    

  def run(self):

    # Get portal
    self.erp5_url = "https://zope:insecure@192.168.242.70:1234/erp5"
    self.portal = xmlrpclib.ServerProxy(self.erp5_url, verbose=False, allow_none=True) 
    # Get access to the distributor
    self.portal_url = self.config['test_suite_master_url']
    self.distributor = xmlrpclib.ServerProxy(
                             self.config['test_suite_master_url'],
                             verbose=False, allow_none=True)

    # Node subscription
    self.distributor.nodeSubscription(self.config['test_node_title'])

    # OptimizeConfiguration (select master + aggregate test_suite)
    self.distributor.optimizeConfiguration()
   
  
    # TODO : (Put the code below into a loop)

    # Determine master and do job

    # TODO : on sever side (or here if it is possible) create
    # a more beautiful way to get the node list
    # This command return empty list sometimes, why ?
    nodes = self.portal.test_node_module.test_node_ben() 

    # what if there are no node recorded into ERP5 Master ?
    # what if there are no master testnode ?
    # what if there are several nodes with the same title ?
    # categories test <=> distributor filter
    self.current_node = [ node for node in nodes
               if node['title'] == self.config['test_node_title'] ][0]
    self.master_node = [ node for node in nodes
               if ( node['master'] == True )
               and ( node['categories'] == self.current_node['categories'] ) ][0]
    self.involved_nodes = [ node for node in nodes
               if ( node['categories'] == self.current_node['categories'] ) ]

    # Master/Slave 
    if self.current_node['title'] == self.master_node['title']:
      self._runAsMaster()
    else:
      self._runAsSlave()

    print "End."
    return

