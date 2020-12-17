#!/usr/bin/env python
# coding: utf-8

import inspect
import functools
class Param2attr:
  def __init__(self, exclude = None, set_extra_args = False, set_extra_kwargs = False):
    self.preprocessExclude(exclude)
    self.set_extra_args = set_extra_args
    self.set_extra_kwargs = set_extra_kwargs

    assert isinstance(self.set_extra_args, bool)
    assert isinstance(self.set_extra_kwargs, bool)

  def preprocessExclude(self, exclude):
    if exclude is None:
      self.exclude = []

    # exclude = "some_string"
    elif isinstance(exclude, str) == 1:
      self.exclude = [exclude]

    else:
      self.exclude = exclude

  def __call__(self, _func):
    functools.wraps(_func)
    def wrapper(obj, *args, **kwargs):

      # boilerplate code
      bound_args = inspect.signature(_func).bind(obj, *args, **kwargs)
      bound_args.apply_defaults()
      dic = dict(bound_args.arguments)
      #print(dic) # uncomment to find contents of dic

      dic.pop('self')
      _args = dic.pop('args', None)
      _kwargs = dic.pop('kwargs', None)

      # setting from dict
      [setattr(obj, key, val) for key, val in dic.items() if key not in self.exclude]
      #setting from extra args
      if self.set_extra_args and _args is not None:
        [setattr(obj, str(key), key) for key in _args if key not in self.exclude]
      #setting from extra kwargs
      if self.set_extra_kwargs and _kwargs is not None:
        [setattr(obj, key, val) for key, val in _kwargs.items() if key not in self.exclude]

      return _func(obj, *args, **kwargs)
    return wrapper


#!pip install -U ez-life


#from ez_life import Param2attr


class Foo:
  def __init__(self, param1 = None, param2 = None, param3 = None):
    # This sux
    self.param1 = param1
    self.param2 = param2
    self.param3 = param3


class Foo:
  @Param2attr(exclude=None)
  def __init__(self, param1 = None, param2 = None, param3 = None):
    # this good, allows u to write other code here during initialization
    pass


if __name__ == '__main__':
  foo = Foo(param1 = "john", param2 = "hog", param3 = "sam")
  assert foo.param1 == "john"
  assert foo.param2 == "hog"
  assert foo.param3 == "sam"


class Foo:
  def __init__(self, param1, param2, param3):
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude=['param1', 'param2'])
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


if __name__ == '__main__':
  foo = Foo("john", "hog", "sam")
  foo_dir = dir(foo)
  assert foo.param3 == "sam"
  assert 'param1' not in foo_dir
  assert 'param2' not in foo_dir


class Foo:
  def __init__(self, param1, param2, param3):
    self.param2 = param2
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude='param1')
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


if __name__ == '__main__':
  foo = Foo("john", "hog", "sam")
  foo_dir = dir(foo)
  assert foo.param2 == "hog"
  assert foo.param3 == "sam"
  assert 'param1' not in foo_dir


class Foo:
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    self.arg1 = arg1
    self.arg2 = arg2
    [setattr(self, str(key), key) for key in args]
    self.kwarg1 = kwarg1
    self.default1 = default1
    [setattr(self, key, val) for key, val in kwargs.items()]


if __name__ == '__main__':
  foo = Foo(1, 'ag2', 'ag3', 4, kwarg1 = 'kwargv1', kwarg2 = 'kwargv2')
  foo_dir = dir(foo)
  arg1 = foo.arg1
  arg2 = foo.arg2
  ag3 = foo.ag3
  foo_4 = getattr(foo, '4') # can't get attribute 4 via foo.4, cause this gives synthax error
  tp_foo_4 = type(getattr(foo, '4'))
  kwarg1 = foo.kwarg1
  kwarg2 = foo.kwarg2
  default1 = foo.default1


class Foo:
  @Param2attr(exclude = None, set_extra_args = True, set_extra_kwargs = True)
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    pass


if __name__=='__main__':
  foo = Foo(1, 'ag2', 'ag3', 4, kwarg1 = 'kwargv1', kwarg2 = 'kwargv2')
  assert foo_dir == dir(foo)
  assert arg1 == foo.arg1
  assert arg2 == foo.arg2
  assert ag3 == foo.ag3
  assert foo_4 == getattr(foo, '4') # can't get attribute 4 via foo.4, gives synthax error
  assert tp_foo_4 == type(getattr(foo, '4'))
  assert kwarg1 == foo.kwarg1
  assert kwarg2 == foo.kwarg2
  assert default1 == foo.default1


class Foo:
  @Param2attr(exclude = None, set_extra_args = False, set_extra_kwargs = False)
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    pass


if __name__=='__main__':
  foo = Foo(1, 'ag2', 'ag3', 4, kwarg1 = 'kwargv1', kwarg2 = 'kwargv2')
  assert arg1 == foo.arg1
  assert arg2 == foo.arg2
  assert 'ag3' not in dir(foo)  
  assert '4' not in dir(foo)
  assert kwarg1 == foo.kwarg1
  assert 'kwarg2' not in dir(foo)
  assert default1 == foo.default1




