
class EzProperty(property):
  """helper property class"""
  def __init__(self, *args, **kwargs):
    return super().__init__(*args, **kwargs)
  
  def setter_preprocess(self, _func):
    """
    Sets return value of _func to self._func.__name__
    """
    def wrapper(obj, val):
      setattr(obj, f"_{_func.__name__}", _func(obj, val))
    return wrapper

  def setter(self, _func):
    """
    calls setter_preprocess wrapper to alter behaviour of _func
    """
    return super().setter(self.setter_preprocess(_func))
    
import functools
class JTProperty:
  def __init__(self, setter = False):
    self.setter = setter
  def __call__(self, _func):
    public_name = _func.__name__
    protected_name = f"_{public_name}"
    
    @EzProperty
    @functools.wraps(_func)
    def wrapper(obj):
      # if self._name is not available atm or self._name is None
      if protected_name not in dir(obj) or getattr(obj, protected_name) is None:
        if (not(self.setter)):
          setattr(obj, protected_name, _func(obj)) 
        else:
          # call setter method with the return value of the property function this effectively sets obj._name
          setattr(obj, public_name, _func(obj)) 
      return getattr(obj, protected_name)
    return wrapper
