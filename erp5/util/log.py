import logging

class DefaultLogger(object):
  logger_format = '%(asctime)s %(name)-13s: %(levelname)-8s %(message)s'

  def __init__(self, id):
    self.logger = logging.getLogger(id)
    logging.basicConfig(level=logging.INFO,
                        format=self.logger_format)

  def __call__(self, message):
    self.logger.info(message)

  def enableConsole(self):
    self.logger.addHandler(logging.StreamHandler())
    self.logger.info('Activated console output.')

  def enableLogFile(self, logfile):
    formatter = logging.Formatter(self.logger_format)
    file_handler = logging.FileHandler(filename=logfile)
    file_handler.setFormatter(formatter)
    self.logger.addHandler(file_handler)
    self.logger.info('Activated logfile %r output' % logfile)
    self.logfile = logfile

  def disableLog(self):
    self.logger.addHandler(logging.NullHandler())

