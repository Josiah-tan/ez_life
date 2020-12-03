#================================================================
#
#   File name   : jt_misc.param2attr.py
#   Author      : Josiah Tan
#   Created date: 28/11/2020
#   Description : module for param2attr class decorator
#
#================================================================

#================================================================

import functools
class Param2attr:
  def __init__(self, exclude = None):
    if exclude is None:
      self.exclude = []

    # exclude = "some string"
    elif isinstance(exclude, str) == 1:
      self.exclude = [exclude]

    else:
      self.exclude = exclude

  def __call__(self, _func):
    functools.wraps(_func)
    def wrapper(obj, *args, **kwargs):
      [setattr(obj, key, val) for key, val in kwargs.items() if key not in self.exclude]
      return _func(obj, *args, **kwargs)
    return wrapper
