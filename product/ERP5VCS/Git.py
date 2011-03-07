# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Julien Muchembled <jm@nexedi.com>
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
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

import os, subprocess
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from DateTime import DateTime
from Products.ERP5Type.Message import translateString
from ZTUtils import make_query
from Products.ERP5VCS.WorkingCopy import \
  WorkingCopy, NotAWorkingCopyError, Dir, File, selfcached

class GitError(EnvironmentError):
  def __init__(self, err, out):
    EnvironmentError.__init__(self, err)
    self.stdout = out

class Git(WorkingCopy):

  security = ClassSecurityInfo()

  reference = 'git'
  title = 'Git'

  def _git(self, *args, **kw):
    kw.setdefault('cwd', self.working_copy)
    argv = ['git']
    return subprocess.Popen(argv + list(args), **kw)

  security.declarePrivate('git')
  def git(self, *args, **kw):
    strip = kw.pop('strip', True)
    p = self._git(stdout=subprocess.PIPE, stderr=subprocess.PIPE, *args, **kw)
    out, err = p.communicate()
    if p.returncode:
      raise GitError(err, out)
    if strip:
      return out.strip()
    return out

  def __init__(self, *args, **kw):
    WorkingCopy.__init__(self, *args, **kw)
    out = self._git('rev-parse', '--show-toplevel', '--show-prefix',
      stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    if not out:
      raise NotAWorkingCopyError(self.working_copy)
    self.toplevel, self.prefix = out.split('\n')[:2]

  def __getitem__(self, key):
    try:
      config = aq_base(self)._config
    except AttributeError:
      self._config = config = {}
      for option in self.git('config', '--list').splitlines():
        k, v = option.split('=', 1)
        config.setdefault(k, []).append(v)
    return config.get(key) or []

  @selfcached
  def _getBranch(self):
    try:
      local, remote = self.git('rev-parse', '--symbolic-full-name',
                               'HEAD', '@{u}').splitlines()
      remote = remote[:13] == 'refs/remotes/' and remote[13:] or None
    except GitError, e:
      local, _ = e.stdout.splitlines()
      remote = None
    assert local[:11] == 'refs/heads/'
    return local[11:], remote

  @selfcached
  def getAheadCount(self):
    """Return number of local commits"""
    # The returned count is for the whole repository.
    # Adding '.' to the command would filter the current directory.
    return int(self.git('rev-list', '--count', '@{u}..'))

  @selfcached
  def getBehindCount(self):
    # XXX: not very useful info
    return int(self.git('rev-list', '--count', '..@{u}'))

  def getRemoteUrl(self):
    remote = self._getBranch()[1]
    if remote:
      url, = self['remote.%s.url' % remote.split('/', 1)[0]]
      return url

  def getRemoteComment(self):
    comment, remote = self._getBranch()
    if remote:
      for key in 'ahead', 'behind':
        count = getattr(self, 'get%sCount' % key.capitalize())()
        if count:
          comment += ', %s: %s' % (key, count)
      return comment
    return 'no remote tracked'

  def addremove(self, added_set, removed_set):
    if added_set:
      self.git('add', '-fN', '--', *added_set)
    #if removed_set:
    #  # this reverts any previous 'git add -N'
    #  self.git('rm', '--ignore-unmatch', '--cached', '--', *removed_set)

  def resolved(self, path_list):
    addremove_list = [], []
    for path in path_list:
      addremove_list[os.path.exists(path)].append(path)
    self.git('add', '--', *addremove_list[1])
    self.git('rm', '--', *addremove_list[0])

  def diff(self, path):
    return self._patch_with_raw()[1].get(path, '')

  @selfcached
  def _patch_with_raw(self):
    out = self.git('diff', '-p', '--raw', '--no-color', '--no-renames',
                  '--no-prefix', '--relative', 'HEAD', '.')
    stat_dict = {}
    diff_dict = {}
    if out:
      out = iter(out.split('\ndiff --git '))
      for stat in out.next().splitlines():
        stat, path = stat.split()[4:]
        stat_dict[path] = stat
      # Emulate svn output for compatibility with Products.ERP5Type.DiffUtils
      template = 'Index: %%s\n%s%%s\n' % ('=' * 67)
      for diff in out:
        path = diff[:diff.index(' ')]
        diff_dict[path] = template % (path, diff[diff.index('\n---'):])
    return stat_dict, diff_dict

  def getModifiedTree(self, show_unmodified=False):
    """ Return tree of files returned by git status
    """
    path_dict = dict.fromkeys(self.git('ls-files').splitlines(), '')
    path_dict.update(self._patch_with_raw()[0])
    node_dict = {}
    path_list = path_dict.keys()
    for path in path_list:
      status = path_dict[path]
      parent = os.path.dirname(path)
      try:
        node_dict[parent].append(path)
      except KeyError:
        node_dict[parent] = [path]
        path_dict[parent] = status
        if parent:
          path_list.append(parent)
      else:
        if path_dict[parent] != status:
          path_dict[parent] = '*'
    status_dict = {'*': 'normal', '': 'normal', 'A': 'added', 'D': 'deleted',
                   'M': 'modified', 'U': 'conflicted'}
    def dir_status(status):
      return status_dict[status in 'AD' and status or '']
    root = Dir(os.path.normpath(self.prefix), dir_status(path_dict['']))
    path_list = [(node_dict.pop(''), root)]
    for content, node in path_list:
      for path in content:
        status = path_dict[path]
        if show_unmodified or status:
          basename = os.path.basename(path)
          try:
            content = node_dict.pop(path)
          except KeyError:
            if status != 'M' or self.hasDiff(path):
              node.sub_files.append(File(basename, status_dict[status]))
          else:
            child = Dir(basename, dir_status(status))
            node.sub_dirs.append(child)
            path_list.append((content, child))
    return (root.sub_dirs or root.sub_files) and root

  def showOld(self, path):
    return self.git('show', 'HEAD:' + self.prefix + path,
                    strip=False, cwd=self.toplevel)

  def getAuthor(self):
    portal = self.getPortalObject()
    author = portal.portal_preferences.getPreferredGitAuthor()
    if author:
      author = author.strip()
      if author:
        return author
    #try:
    #  author = portal.ERP5Site_getAuthenticatedMemberPersonValue()
    #  name = author.getTitle()
    #  email = author.getDefaultEmailText()
    #  if name and email:
    #    return '%s <%s>' % (name, email)
    #except AttributeError:
    #  pass

  def commit(self, changelog, added=(), modified=(), removed=()):
    context = self.aq_parent
    request = context.REQUEST

    selected_set = set(added)
    selected_set.update(modified)
    selected_set.update(removed)
    # remove directories from selected_set
    selected_set.intersection_update(self._patch_with_raw()[0])
    args = ['commit', '-m', changelog, '--']
    author = self.getAuthor()
    if author:
      args[1:1] = '--author', author
    self.git(*(args + list(selected_set)))
    try:
      if request.get('push'):
        src, remote = self._getBranch()
        remote, dst = remote.split('/', 1)
        self.git('push', '--porcelain', remote, '%s:%s' % (src, dst))
    except GitError, e:
      self.git('reset', '--soft', '@{1}')
      portal_status_message = str(e)
    else:
      head = self.git('rev-parse', '--short', 'HEAD')
      portal_status_message = translateString(
        'Files committed successfully in revision ${revision}',
        mapping=dict(revision=head))
    return request.RESPONSE.redirect('%s/view?%s' % (
      context.absolute_url_path(),
      make_query(portal_status_message=portal_status_message)))

  def log(self, path='.'):
    log = []
    for commit in self.git('log', '-z', '--pretty=format:%h%n%at%n%aN%n%B',
                           '--', path, strip=False).split('\0'):
      revision, date, author, message = commit.split('\n', 3)
      log.append(dict(revision=revision,
                      date=DateTime(int(date)),
                      author=author,
                      message=message))
    return log

  def _clean(self):
    # XXX unsafe if user doesn't configure files to exclude
    self.git('clean', '-fd', cwd=self.toplevel)