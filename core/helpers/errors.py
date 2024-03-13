# -*- coding:utf-8 -*-
# @module logger
# @since 2024.03.12, 18:01
# @changed 2024.03.12, 18:08


import traceback


def errorToString(error, show_stacktrace=False):
    """
    Convert error object to string
    """
    errorName = type(error).__name__
    errorExtra = str(error)
    errorArg = str(error.args[0]) if error.args and error.args[0] else ''
    if errorArg and errorArg != errorExtra:
        errorExtra += ' (' + errorArg + ')'
    errorStr = errorName + ': ' + errorExtra
    if show_stacktrace:
        stack = traceback.format_exc()
        if stack:
            errorStr += '\n' + stack
    return errorStr


#  # UNUSED: errorToBlockString
#  def errorToBlockString(error):
#      errorStr = errorToString(error)
#      return yamlSupport.BlockString(errorStr)


__all__ = [  # Exporting objects...
    'errorToString',
    #  'errorToBlockString',
]
