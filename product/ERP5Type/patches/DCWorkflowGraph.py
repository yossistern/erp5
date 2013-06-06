# -*- coding: utf-8 -*-

def getObjectTitle(obj, REQUEST=None):
  """
  Get a state/transition title to be displayed in the graph.

  Monkey-patched to support translation similar to what
  Products.ERP5Type.Accessor.WorkflowState.TranslatedGetter does
  """
  if REQUEST is not None:
    only_ids = REQUEST.get('only_ids', False)
    translate = REQUEST.get('translate', False)
  else:
    only_ids = False
    translate = False

  _id = obj.getId()
  title = obj.title
  if not title or only_ids:
    title = _id
  else:
    if translate:
      # Translate the title in all supported Localizer languages
      wf_id = obj.getWorkflow().id
      localizer = obj.Localizer
      original_title = title
      for lang in localizer.get_supported_languages():
        msg_id = '%s [state in %s]' % (title, wf_id)
        translated_title = localizer.erp5_ui.gettext(
          msg_id,
          lang=lang,
          # Fallback on non-workflow state translation
          default=localizer.erp5_ui.gettext(original_title,
                                            lang=lang,
                                            default=None))

        if (translated_title is not None and
            translated_title != original_title):

          title += "\\n%s" % translated_title

    title += "\\n(%s)"% _id

  return title

from Products.DCWorkflowGraph import DCWorkflowGraph
DCWorkflowGraph.getObjectTitle = getObjectTitle

from Products.DCWorkflowGraph.config import bin_search_path, DOT_EXE
from tempfile import mktemp
import os

def getGraph(self, wf_id="", format="png", REQUEST=None):
    """show a workflow as a graph, copy from:
"OpenFlowEditor":http://www.openflow.it/wwwopenflow/Download/OpenFlowEditor_0_4.tgz

    Monkey-patched to specify font name and size as 'dot' uses Times font by
    default which does not support Japanese:

    http://www.graphviz.org/doc/fontfaq.txt

    Another solution would be to modify fontconfig configuration so that Times
    match Japanese font or to use Unifont which supports many code points.

    """
    try:
      pot = DCWorkflowGraph.getPOT(self, wf_id, REQUEST)
    except TypeError:
      # DCWorkflowGraph < 0.4
      pot = DCWorkflowGraph.getPOT(self, wf_id)
    try:
        encoding = self.portal_properties.site_properties.getProperty('default_charset', 'utf-8')
    except AttributeError:
        # no portal_properties or site_properties, fallback to:
        encoding = self.management_page_charset.lower()
    pot = pot.encode(encoding)
    infile = mktemp('.dot')
    with open(infile, 'w') as f:
      f.write(pot)
    
    if REQUEST is None:
        REQUEST = self.REQUEST
    response = REQUEST.RESPONSE
        
    if format != 'dot':
        outfile = mktemp('.%s' % format)
        os.system('%s -Nfontname="IPAexGothic" -Nfontsize=10 '
                  '-Efontname="IPAexGothic" -Efontsize=10 -T%s '
                  '-o %s %s' % (DCWorkflowGraph.bin_search(DOT_EXE),
                                format, outfile, infile))
        with open(outfile, 'rb') as out:
          result = out.read()
        os.remove(outfile)
        response.setHeader('Content-Type', 'image/%s' % format)
    else:
        with open(infile, 'r') as out:
          result = out.read()
        filename = wf_id or self.getId()
        response.setHeader('Content-Type', 'text/x-graphviz')
        response.setHeader('Content-Disposition',
                           'attachment; filename=%s.dot' % filename)
        
    os.remove(infile)
    return result

from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
DCWorkflowDefinition.getGraph = getGraph
