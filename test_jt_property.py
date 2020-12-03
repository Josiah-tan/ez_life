
#================================================================
#
#   File name   : test_jt_property.py
#   Author      : Josiah Tan
#   Created date: 3/12/2020
#   Description : testing jt_property module from ez_life
#
#================================================================

#================================================================
from ez_life import JTProperty
class PropDemo:
  def __init__(self):
    self._prop1 = None
    self._prop2 = None
    self._prop3 = None
  
  @property
  def prop1(self):
    if self._prop1 is None:
      self._prop1 = self.get_prop1()
    return self._prop1

  @property
  def prop2(self):
    if self._prop2 is None:
      self._prop2 = self.get_prop2()
    return self._prop2

  @property
  def prop3(self):
    if self._prop3 is None:
      self._prop3 = self.get_prop3()
    return self._prop3
  
  def get_prop1(self):
    return 1
  def get_prop2(self):
    return self.prop1 + 1
  def get_prop3(self):
    return self.prop2 + 1

prop_dem = PropDemo()
print(prop_dem.prop3)

"""- The @JTProperty decorator uses less lines of code then the @property decorator, but achieves the same result"""

class JTPropDemo:
  def __init__(self):
    pass
  
  @JTProperty()
  def prop1(self):
    return 1

  @JTProperty()
  def prop2(self):
    return self.prop1 + 1

  @JTProperty()
  def prop3(self):
    return self.prop2 + 1

prop_dem = JTPropDemo()
print(prop_dem.prop3)

"""# Setter methods
- Consider a class that uses getter and setter methods as shown below:
"""

class SetAndGet:
  def __init__(self, r = 1):
    # initialise the protected variable
    self._radius = None

    # calls the @radius.setter method
    self.radius = r
  @property
  def radius(self):
    if self._radius is None:
      self.radius = 2
    return self._radius
  @radius.setter
  def radius(self, r):
    if r <= 0:
      raise ValueError("radius should be greater than 0")
    self._radius = r

"""- In the test below, contextlib silences the ValueError that occurs with setting the radius to -5"""

import contextlib
setandget = SetAndGet()
print(setandget.radius)
setandget.radius = 5
print(setandget.radius)
setandget.radius = 3
print(setandget.radius)
with contextlib.suppress(ValueError):
  setandget.radius = -5
print(setandget.radius)

"""- JTProperty() and .setter reduce abstraction involving usage of hidden "protected variables"
  - setter = True should be set when @radius.setter is used
"""

class JTSetAndGet:
  def __init__(self, r = 1):
    self.radius = r
  @JTProperty(setter = True)
  def radius(self):
    return 2

  @radius.setter
  def radius(self, r):
    if r <= 0:
      raise ValueError("radius should be greater than 0")
    return r

import contextlib

setandget = JTSetAndGet()
print(setandget.radius)
setandget.radius = 5
print(setandget.radius)
setandget.radius = 3
print(setandget.radius)
with contextlib.suppress(ValueError):
  setandget.radius = -5
print(setandget.radius)
