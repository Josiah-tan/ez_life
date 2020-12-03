
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
    self._prop = None
    @EzProperty
    @functools.wraps(_func)
    def wrapper(obj):
      # case where the .setter is not used
      if not(self.setter):
        if self._prop is None:
          self._prop = _func(obj)
        return self._prop
      # case where .setter is used
      else:
        # if self._name is not available atm
        if f"_{_func.__name__}" not in dir(obj):
          # call setter method with the return value of the property function this effectively sets obj._name
          setattr(obj, _func.__name__, _func(obj)) 
        # get the obj._name variable
        self._prop = getattr(obj, f"_{_func.__name__}")
        return self._prop
    return wrapper