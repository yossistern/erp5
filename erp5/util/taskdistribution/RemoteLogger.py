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
from datetime import datetime
import time

from erp5.util.taskdistribution import TaskDistributionClient

class RemoteLogger(object):

  def __init__(self, log, log_file, test_node_title, process_manager=None):
    self.portal = None
    self.test_result_path = None
    self.test_node_title = test_node_title
    self.log = log
    self.log_file = log_file
    self.process_manager = process_manager
    self.finish = False
    self.quit = False

  def update(self, portal, test_result_path):
    self.portal = portal
    self.test_result_path = test_result_path

  def getSize(self):
    erp5testnode_log = open(self.log_file, 'r')
    try:
      erp5testnode_log.seek(0, 2)
      size = erp5testnode_log.tell()
    finally:
      erp5testnode_log.close()
    return size

  def __call__(self):
    size = self.getSize()
    while True:
      for x in xrange(0,60):
        if self.quit or self.finish:
          break
        time.sleep(1)
      if self.quit:
        return
      finish = retry = self.finish
      if self.test_result_path is None:
        if finish:
          return
        continue
      start_size = size
      end_size = self.getSize()
      # file was truncated
      if end_size < start_size:
        size = end_size
        continue
      # display some previous data
      if start_size >= 5000:
        start_size -= 5000
      # do not send tons of log, only last logs
      if (end_size-start_size >= 10000):
        start_size = end_size - 10000
      erp5testnode_log = open(self.log_file, 'r')
      try:
        erp5testnode_log.seek(start_size)
        output = erp5testnode_log.read()
      finally:
        erp5testnode_log.close()

      if end_size == size:
        output += '%s : stucked ??' % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
      # check if the test result is still alive
      task_distribution_client = TaskDistributionClient(self.portal, self.log)
      is_alive = task_distribution_client.isTaskAlive(self.test_result_path, retry=False)
      self.log('isTaskAlive result %r' % is_alive)
      if is_alive is not None  and is_alive == 0:
        self.log('Test Result cancelled on server side, stop current test')
        if self.process_manager is None:
          self.log('Unable to invoke kill previous run on ProcessManager, ' +\
                   'self.process_manager is None.')
          return
        self.process_manager.killPreviousRun(cancellation=True)
        return
      status_dict = dict(command='erp5testnode', status_code=0,
                         stdout=''.join(output), stderr='')
      task_distribution_client.reportTaskStatus(self.test_result_path, status_dict, 
                                                self.test_node_title, retry=retry)
      size = end_size
      if finish:
        return

