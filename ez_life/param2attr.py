#!/usr/bin/env python
# coding: utf-8

# <a href="https://colab.research.google.com/github/Josiah-tan/ez_life/blob/main/ez_life/param2attr.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# # Implementation 
# - Code below implements the desired features for the param2attr idea to make code more concise

# In[15]:


import inspect
import functools
class Param2attr:
  def __init__(self, exclude = None):
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
      if _args is not None:
        [setattr(obj, str(key), key) for key in _args if key not in self.exclude]
      #setting from extra kwargs
      if _kwargs is not None:
        [setattr(obj, key, val) for key, val in _kwargs.items() if key not in self.exclude]

      return _func(obj, *args, **kwargs)
    return wrapper


# # Param2attr
# - The objective of this class decorator is to automate creation of class attributes from arguments passed into an \_\_init\_\_ method 
# - Say we have a class that looks like this:

# In[16]:


class Foo:
  def __init__(self, param1 = None, param2 = None, param3 = None):
    # This sux
    self.param1 = param1
    self.param2 = param2
    self.param3 = param3


# - We can instead create a class that looks like this, using a property decorator to perform the param to attribute assignments

# In[17]:


class Foo:
  @Param2attr(exclude=None)
  def __init__(self, param1 = None, param2 = None, param3 = None):
    # this good, allows u to write other code here during initialization
    pass


# In[18]:


if __name__ == '__main__':
  foo = Foo(param1 = "john", param2 = "hog", param3 = "sam")
  assert foo.param1 == "john"
  assert foo.param2 == "hog"
  assert foo.param3 == "sam"


# # Exclude
# - The optional exclude parameter excludes any parameters in creating attributes for the class
#   - You can specify this as a list

# In[19]:


class Foo:
  def __init__(self, param1, param2, param3):
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude=['param1', 'param2'])
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


# In[20]:


if __name__ == '__main__':
  foo = Foo("john", "hog", "sam")
  foo_dir = dir(foo)
  assert foo.param3 == "sam"
  assert 'param1' not in foo_dir
  assert 'param2' not in foo_dir


# - You can also specify the exclude param as a string

# In[21]:


class Foo:
  def __init__(self, param1, param2, param3):
    self.param2 = param2
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude='param1')
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


# In[22]:


if __name__ == '__main__':
  foo = Foo("john", "hog", "sam")
  foo_dir = dir(foo)
  assert foo.param2 == "hog"
  assert foo.param3 == "sam"
  assert 'param1' not in foo_dir


# # The General Case
# - The code below exhibits how @Param2attr can be used in general scenarios
#   - First we will show the traditional, hardcoded implementation

# In[23]:


class Foo:
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    self.arg1 = arg1
    self.arg2 = arg2
    [setattr(self, str(key), key) for key in args]
    self.kwarg1 = kwarg1
    self.default1 = default1
    [setattr(self, key, val) for key, val in kwargs.items()]


# In[24]:


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


# - The code below does the same thing, but is simplified via the @Param2attr decorator

# In[25]:


class Foo:
  @Param2attr(exclude = None)
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    pass


# In[26]:


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


# In[26]:




