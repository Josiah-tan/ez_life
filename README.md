# ez\_life
The objective of ez\_life is to make coding with Python easier by removing repetitive code while still maintaining the same level of functionality

# Installation
```
pip install -U ez_life
```
# param2attr
- Here is a little sneak peak of what you can do with this package!
	- First consider this code block:


```python
from ez_life import Param2attr

class Foo:
	def __init__(self, param1 = None, param2 = None, param3 = None):
		# This sux
			self.param1 = param1
			self.param2 = param2
			self.param3 = param3
```

- We can instead create a class that looks like this, using a property decorator to perform the param to attribute assignments 

```python
class Foo:
	@Param2attr(exclude=None) 
	def __init__(self, param1 = None, param2 = None, param3 = None): 
		# this good, allows u to write other code here during initialization 
		pass
```

- If you are interested to learn about the implementation or other features that param2attr supports, feel free to read the [Param2attr documentation](https://colab.research.google.com/drive/1PStbTEDiuXgjIKrMOcJAbY9NOg23w9TK?usp=sharing)!

# JTProperty

- Ez\_life can also be used to create "variable dependencies" using the @JTProperty decorator
	- It essentially builds upon the functionality that the @property decorator gives!

## Understanding The Classic @property:

- The concept of python's classic decorator @property is not difficult to learn, read this section if you want to learn it or get a refresher

### Classic Setter and Getter Methods

- First consider a classic class Square
	- A square has a 3 properties: 
		- A length, an perimeter and an area
	- First we will code the length:

```python
class Square:
	def getLength(self):
		return self._length # the underscore "_" in "_length" means that it is a "protected variable"
	
	def setLength(self, r):
    if r <= 0:
      raise ValueError("length should be greater than 0")
		self._length = r
```
- We can use this class as follows:

```python
square = Square() # create a class instance
square.setLength(4) # sets self._length to 4
print(square.getLength()) # 4
square.setLength(-1) # raises a ValueError "length should be greater than 0"
```
### Property Setter and Getter Methods Part 1

- Python's inbuilt @property decorator allows setters and getters to be used in a much easier way:

```python
class Square:
	@property
	def length(self): # the setter method
		return self._length
	
	@length.setter
	def length(self, r): # the getter method
    if r <= 0:
      raise ValueError("length should be greater than 0")
		self._length = r
```
- The code below shows how to use the setter and getter methods for this class:

```python
square = Square() # create a square instance
square.length = 4 # sets self._length to 4
print(square.length) # 4
square.length = -1 # raises a ValueError "length should be greater than 0"
```
- Syntactically, the code above is much more pythonic, but the problem is that the setter must be called before the getter
	- The code below demonstrates this vulnerability:

```python
square = Square() 
print(square.length) # raises an error
```
### Property Setter and Getter Methods Part 2 

- The reason why an error is raised is because the length has not been set yet via the setter method
	- A solution to this could be achieved as follows:

```python 
class Square:
	@property
	def length(self):
		if "_length" not in dir(self): # checks if self._length is an attribute yet
			self.length = 1 # if not, call the setter method to set self._length to 1
		return self._length
	
	@length.setter
	def length(self, r):
    if r <= 0:
      raise ValueError("length should be greater than 0")
		self._length = r
```

- Now we will not get an error when calling the getter before the setter, we instead get some default value
	- In this case the default value is 1


```python
square = Square() 
print(square.length) # 1
```

## Understanding The @JTProperty:

### JTProperty Setter and Getter Methods

- Obviously, the code with the @property decorator is Pythonic, however it is far from perfect
	- We can see that there are many lines of code already written for just the length setter and getter methods 
- Now we will demonstrate how the ez\_life @JTProperty decorator can make the Square class above more concise 
	- @JTProperty does this by abstracting away the self.\_length variable

```python
# importing the JTProperty decorator from the ez_life module
from ez_life import JTProperty 

class Square:
  @JTProperty()
  def length(self):
    return 1

  @length.setter
  def length(self, r):
    if r <= 0:
      raise ValueError("length should be greater than 0")
    return r
```
- For JTProperty we can call the setter before the getter method

```python 
square = Square() # create a class instance
square.length = 4 # sets self._length to 4
print(square.length) # 4
square.length = -1 # raises a ValueError "length should be greater than 0"
```

- Or we can call the getter before the setter method

```python
square = Square() 
print(square.length) # 1
```

- As we can see, JTProperty offers the same functionality as @property but with less code!

### Full Implementation of Square with JTProperty

- Now that we have an understanding of JTProperty, we can fully implement the square class perimeter and area setter methods!

```python
class Square: 
	@JTProperty()
  def length(self):
    return 1

  @length.setter
  def length(self, r):
    if r <= 0:
      raise ValueError("length should be greater than 0")
    return r

	@JTProperty()
	def area(self):
		return self.length ** 2
	
	@JTProperty()
	def perimeter(self):
		return self.length * 4
```

- We can call these methods as follows:

```python
square = Square()
print(square.area) # (1 ** 2) => 1
print(square.perimeter) # (1 * 4) => 4

square.length = 2 # set length to 2

print(square.area) # 1 <= note that square.area stays the same even though square.length changed
print(square.perimeter) # 4 <= note that square.perimeter stays the same

# square.area = 10 # (note that this gives an error because no setter method is defined for area)
```

### Full Implementation of Square with JTProperty part 2 (with dependencies)

- Notice that square.area and square.perimeter do not update when square.length is changed to 2
	- To update square.area and square.perimeter when square.length is changed, a "dependency" list must be given to JTProperty for both square.area and square.perimeter methods:

```python
class Square:
  @JTProperty()
  def length(self):
    return 1

  @length.setter
  def length(self, r):
    if r <= 0:
      raise ValueError("length should be greater than 0")
    return r

	@JTProperty(deps = 'length')
	def area(self):
		return self.length ** 2
	
	@JTProperty(deps = 'length')
	def perimeter(self):
		return self.length * 4
```

- Now when changing square.length to some other value, both square.area and square.perimeter return their corresponding updated values when called

```python
square = Square()
print(square.area) # (1 ** 2) => 1
print(square.perimeter) # (1 * 4) => 4

square.length = 2 # set length to 2

print(square.area) # (2 ** 2) => 4
print(square.perimeter) # (2 * 4) => 8
```

- This concludes the introduction to some of the features that JTProperty supports!
- Other features not covered here include:
	- Support for hierarchal classes
	- default and default type setters
	- Circular dependency graphs
- If you are interested to learn about these other features and more, feel free to read the [JTProperty documentation](https://colab.research.google.com/drive/1yt7lT1H9xhXY7OVo7DGaW-APm-qHWOpR?usp=sharing)!

# ez-life directory layout:

- develop: the package containing all .ipynb dev files and converted .py files
	- param2attr.ipynb: dev notebook for automation of parameter creation to class object attributes
	- param2attr.py: param2attr.ipynb -> param2attr.py via Makefile
	- jt\_property.ipynb: dev notebook for more writing dependency related code
	- jt\_property.py: jt\_property.ipynb -> jt\_property.py via Makefile
- ez\_life: the package containing all converted .py files
- .gitignore: for ignoring files when pushing and pulling
- LICENSE: what u can and can't do with this repo
- MAKEFILE: automated test cases and .ipynb to .py conversion
- README: this file essentially
- MANIFEST.in: Files to include in pip upload
- build: automatically generated file for pip 
- dist: automatically generated file for pip 
- setup.py: contains setups for when uploading to pip
- test*.py: test files for modules within ez_life

