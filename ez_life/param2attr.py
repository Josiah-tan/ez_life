#!/usr/bin/env python
# coding: utf-8

# <a href="https://colab.research.google.com/github/Josiah-tan/ez_life/blob/main/param2attr.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# # Implementation 
# - Code below implements the desired features for the param2attr idea to make code more concise

# In[4]:


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


# In[7]:


class Foo:
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    self.arg1 = arg1
    self.arg2 = arg2
    [setattr(self, str(key), key) for key in args]
    self.kwarg1 = kwarg1
    self.default1 = default1
    [setattr(self, key, val) for key, val in kwargs.items()]


# In[8]:


foo = Foo(1, 'ag2', 'ag3', 4, kwarg1 = 'kwargv1', kwarg2 = 'kwargv2')
print(dir(foo))
print(foo.arg1)
print(foo.arg2)
print(foo.ag3)
print(getattr(foo, '4')) # can't get attribute 4 via foo.4, gives synthax error
print(type(getattr(foo, '4')))
print(foo.kwarg1)
print(foo.kwarg2)
print(foo.default1)


# In[9]:


class Foo:
  @Param2attr(exclude = None)
  def __init__(self, arg1, arg2, *args, kwarg1 = 'kwg1', default1 = 'optkwg1', **kwargs):
    pass


# In[10]:


foo = Foo(1, 'ag2', 'ag3', 4, kwarg1 = 'kwargv1', kwarg2 = 'kwargv2')
print(dir(foo))
print(foo.arg1)
print(foo.arg2)
print(foo.ag3)
print(getattr(foo, '4')) # can't get attribute 4 via foo.4, gives synthax error
print(type(getattr(foo, '4')))
print(foo.kwarg1)
print(foo.kwarg2)
print(foo.default1)


# # Param2attr
# - The objective of this class decorator is to automate creation of class attributes from kwargs passed into an \_\_init\_\_ method 
#   - (note: this does not work for args)
# - Say we have a class that looks like this:

# In[ ]:


class Foo:
  def __init__(self, param1 = None, param2 = None, param3 = None):
    # This sux
    self.param1 = param1
    self.param2 = param2
    self.param3 = param3


# - We can instead create a class that looks like this, using a property decorator to perform the param to attribute assignments

# In[ ]:


class Foo:
  @Param2attr(exclude=None)
  def __init__(self, param1 = None, param2 = None, param3 = None):
    print("hello")


# In[ ]:


foo = Foo(param1 = "john", param2 = "hog", param3 = "sam")
dir(foo)[-4:]


# # Exclude
# - The optional exclude parameter excludes any parameters in creating attributes for the class
#   - You can specify this as a list

# In[ ]:


class Foo:
  def __init__(self, param1, param2, param3):
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude=['param1', 'param2'])
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


# In[ ]:


foo = Foo(param1 = "john", param2 = "hog", param3 = "sam")
dir(foo)[-3:]


# - You can also specify the exclude param as a string

# In[ ]:


class Foo:
  def __init__(self, param1, param2, param3):
    self.param3 = param3

# is the same as

class Foo:
  @Param2attr(exclude='param1')
  def __init__(self, param1 = None, param2 = None, param3 = None):
    pass


# In[ ]:


foo = Foo(param1 = "john", param2 = "hog", param3 = "sam")
dir(foo)[-3:]


# In[ ]:





# In[ ]:




