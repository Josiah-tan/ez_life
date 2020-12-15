#!/usr/bin/env python
# coding: utf-8

import functools
import sys
import threading


class Node:
  def __init__(self, data):
    self.data = data
    self.was_visited = False
    self._edges = set()

  def addEdge(self, edges):
    assert isinstance(edges, set)
    self._edges.update(edges) 


class Graph:
  def __init__(self, cls_name):
    self.cls_name = cls_name
    self.data2node = {}

  def data2Node(self, data):
    node = self.data2node.get(data, None)
    if node is None:
      node = Node(data)
      self.data2node[data] = node
    return node

  def add(self, out, into):
    out = out if isinstance(out, list) else {out}
    into = into if isinstance(into, list) else {into}

    outNodes = {self.data2Node(o) for o in out}
    intoNodes = {self.data2Node(i) for i in into}

    for outNode in outNodes:
      outNode.addEdge(intoNodes)
  
  def disp(self):
    print("displaying graph")
    for data, node in self.data2node.items():
      print(f"{data} points to {set(n.data for n in node._edges)}")

  
  def resetDepDFS(self, obj, protected_name):
    """
    Runs a DFS alrgorithm on the graph datastructure to reset all downstream dependencies to None
    """
    node = self.data2Node(protected_name)

    def recursiveReset(node):
      if (not isinstance(node, Node)) or node.was_visited:
        return
      node.was_visited = True
      if (node.data in dir(obj)) and getattr(obj, node.data) is not None: # added this here so that recursion stops when the attribute is already None such that downstream dependencies are not reset since they are assumed to be also None, or preset to some value 
        setattr(obj, node.data, None)
        [recursiveReset(n) for n in node._edges]
  
    recursiveReset(node)

    for n in self.data2node.values():
      n.was_visited = False


class DefaultSetter:
    def __init__(self, setter):
      self.setter = setter
    def __call__(self, _func):
      if str(self.setter).lower() in "default":
        _func = _func.setter(defaultSetter)
      return _func


def EzProperty(JTProperty_obj):
  class ClsWrapper(property):
    def __init__(self, *args, **kwargs):
      return super().__init__(*args, **kwargs)
    
    def setter_preprocess(self, _func):
      """
      Performs preprocessing on the self._func decorated by @func.setter
        - resets all downstream graph dependencies
        - sets return value of _func to protected name of _func
      """
      def wrapper(obj, val):
        #JTProperty_obj.firstBeforeS_Get()
        JTProperty_obj.joinClsThreads()

        JTProperty_obj.cls_name2graph[JTProperty_obj.cls_name].resetDepDFS(obj, JTProperty_obj.protected_name)
        setattr(obj, JTProperty_obj.protected_name, _func(obj, val))
        #print(getattr(obj, protected_name))
      return wrapper
  
    def setter(self, _func):
      """
      calls setter_preprocess wrapper to alter behaviour of _func
      """
      return super().setter(self.setter_preprocess(_func))
  return ClsWrapper


def defaultSetter(obj, var):
  return var

class JTProperty:

  # dicts for clsWasDeclared multithreading
  cls_name2cls = {}
  cls_name2thread = {}
  cls_name2active_t = {} # stores currently active threads

  # dict of class names (str) that have been decorated with JTProperty
  cls_name2graph = {}
  def __init__(self, setter = False, deps = None):
    # Tri state "setter": True, Default, False
    self.setter = setter
    self.deps = self.preprocessDeps(deps)
  
  def preprocessDeps(self, deps):
    """
    converts all deps to protected string variables
    """
    if deps is None:
      return None
    elif not isinstance(deps, (list, set)):
      deps = [deps]
    #check if all dependencies are either a string (or a EzProperty instance <- not implemented)
    assert all(isinstance(dep, (str)) for dep in deps)
    return [f"_{dep}" for dep in deps]

  def getVar(self, obj):
    # if self._name is not available atm or it is set to None
    if (self.protected_name not in dir(obj)) or (getattr(obj, self.protected_name) is None):
      if self.setter == False:
        setattr(obj, self.protected_name, self._func(obj)) 
      else:
        # call setter method obj.name with the return value of the property function, this effectively sets obj._name
        setattr(obj, self.public_name, self._func(obj)) 
    return getattr(obj, self.protected_name)

  def createDepGraph(self):
    cls_graph = self.cls_name2graph.get(self.cls_name, None)
    if cls_graph is None:
      self.cls_name2graph[self.cls_name] = Graph(self.cls_name)

    if self.deps is not None:
      self.cls_name2graph[self.cls_name].add(out = self.deps, into = self.protected_name)
      #self.cls_name2graph[cls_name].disp()

  def __call__(self, _func):
    self._func = _func
    self.public_name = _func.__name__
    self.protected_name = f"_{self.public_name}"

    self.cls_name = _func.__qualname__.rsplit('.', 1)[0]
    #cls = inspect._findclass(_func) <- big annoying problem: can't get cls from _func within this __call__ method, cls is not a global variable yet

    self.createDepGraph()

    # the getter method here
    @DefaultSetter(self.setter)
    @EzProperty(self)
    @functools.wraps(_func)
    def wrapper(obj):
      #might need something here to connect nodes with inherited classes
      self.joinClsThreads()
      #self.firstBeforeS_Get()
      return self.getVar(obj)

    # perform tasks after cls is declared (run this last to reduce busy waiting load)
    self.clsWasDeclared()
    return wrapper

  def clsWasDeclared(self):
    def cls_name2Cls():
      # Need someone to help me make a better listener than this plz
      while self.cls_name not in dir(sys.modules.get(self._func.__module__)):
        pass

      # essentially the same thing as in inspect.py -> _findclass() 
      cls = sys.modules.get(self._func.__module__)
      for name in self.cls_name.split('.'):
        cls = getattr(cls, name) 

      self.cls_name2cls[self.cls_name] = cls #getattr(sys.modules.get(self._func.__module__), self.cls_name)
    
    # we only run this block once for the first decorated method in the class
    if self.cls_name2thread.get(self.cls_name, None) is None:
      #NOTE! Might need to join pre-existing threads somewhere in the code, maybe
      self.cls_name2thread[self.cls_name] = threading.Thread(target = cls_name2Cls)
      self.cls_name2thread[self.cls_name].start()

      self.cls_name2active_t[self.cls_name] = self.cls_name2thread[self.cls_name] # to denote that its running

  def joinClsThreads(self):
    while len(self.cls_name2active_t) != 0:
      cls_name, active_t = self.cls_name2active_t.popitem()
      active_t.join()

    #for cls_name, thread in self.cls_name2thread.items():
      #thread.join()
    """
    thread = self.cls_name2thread.get(self.cls_name, None)
    if thread is None:
      pass
    else:
      thread.join()
    """


if __name__ == '__main__':
  def print_assert(p, a = None):
    print(p)
    if a is not None:
      assert p.__str__() == a


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
  


if __name__ == '__main__':
  prop_dem = PropDemo()
  print_assert(prop_dem.prop3, '3')


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
  


if __name__ == '__main__':
  prop_dem = JTPropDemo()
  print_assert(prop_dem.prop3, '3')


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


if __name__ == '__main__':
  import contextlib
  setandget = SetAndGet()
  #print(setandget.radius)
  print_assert(setandget.radius, '1')

  setandget.radius = 5
  #print(setandget.radius)
  print_assert(setandget.radius, '5')

  setandget.radius = 3
  #print(setandget.radius)
  print_assert(setandget.radius, '3')

  with contextlib.suppress(ValueError):
    setandget.radius = -5
  #print(setandget.radius)
  print_assert(setandget.radius, '3')


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


if __name__ == '__main__':
  import contextlib
  setandget = SetAndGet()
  print_assert(setandget.radius, '1')

  setandget.radius = 5
  print_assert(setandget.radius, '5')

  setandget.radius = 3
  print_assert(setandget.radius, '3')

  with contextlib.suppress(ValueError):
    setandget.radius = -5
  print_assert(setandget.radius, '3')


# writing the setter explicitly
class SetterDemo:
  @JTProperty(setter=True)
  def prop(self):
    return 1
  
  @prop.setter
  def prop(self, val):
    return val


if __name__ == "__main__":
  # test setter before getter
  setter_demo = SetterDemo()
  setter_demo.prop = 2
  print_assert(setter_demo.prop, '2')


if __name__ == "__main__":
  # test getter before setter
  setter_demo = SetterDemo()
  print_assert(setter_demo.prop, '1')


# writing the setter implicitly
class AutoSetterDemo:
  @JTProperty(setter="Default")
  def prop(self):
    return 1


if __name__ == "__main__":
  # test setter before getter
  auto_setter_demo = AutoSetterDemo()
  auto_setter_demo.prop = 2
  print_assert(auto_setter_demo.prop, '2')


if __name__ == "__main__":
  # test getter before setter
  auto_setter_demo = AutoSetterDemo()
  print_assert(auto_setter_demo.prop, '1')


class GraphDemo:
  @JTProperty(setter = "Default")
  def a(self):
    return 'a'

  @JTProperty(setter = "Default", deps = 'a')
  def b(self):
    return self.a + '->b'
  
  @JTProperty(setter = "Default")
  def c(self):
    return 'c'

  @JTProperty(setter = "Default", deps = ['c', 'b'])
  def d(self):
    return self.b + '->d' + ' and ' + self.c + '->d'


if __name__ == '__main__':
  graph_demo = GraphDemo()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph[type(graph_demo).__name__].disp()
  #displaying graph
  #_a points to {'_b'}
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()


if __name__ == '__main__':
  graph_demo = GraphDemo()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph[type(graph_demo).__name__].disp()
  #displaying graph
  #_a points to {'_b'}
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()


class GraphDemo2:
  @JTProperty(setter = "Default", deps = ['b', 'd'])
  def a(self):
    return self.b + '->a and ' + self.d + '->a'

  @JTProperty(setter = "Default", deps = 'a')
  def b(self):
    return self.a + '->b'
  
  @JTProperty(setter = "Default", deps = 'b')
  def c(self):
    return self.b + '->c'

  @JTProperty(setter = "Default", deps = ['c'])
  def d(self):
    return self.c + '->d'


if __name__ == '__main__':
  graph_demo = GraphDemo2()
  JTProperty.cls_name2graph[type(graph_demo).__name__].disp()
  #displaying graph
  #_b points to {'_c', '_a'}
  #_a points to {'_b'}
  #_c points to {'_d'}
  #_d points to {'_a'}

  # tests if setter for .b resets ._a accidentally
  graph_demo = GraphDemo2()
  graph_demo.a = 'a'
  print_assert(graph_demo.a, 'a')
  print_assert(graph_demo.b, 'a->b')
  print_assert(graph_demo._a, 'a')
  
  graph_demo = GraphDemo2()
  print("graph_demo.a = 'a':")
  graph_demo.a = 'a'
  print_assert(graph_demo.b, 'a->b')
  print_assert(graph_demo.c, 'a->b->c')
  print_assert(graph_demo.d, 'a->b->c->d')
  
  graph_demo = GraphDemo2()
  print("graph_demo.b = 'b':")
  graph_demo.b = 'b'
  print_assert(graph_demo.d, 'b->c->d')
  print_assert(graph_demo._b, 'b')
  print_assert(graph_demo.a, 'b->a and b->c->d->a')
  print_assert(graph_demo.c, 'b->c')
  
  # Causes Recursion problems (intentional) <- a and b must be preset since they are dependent on each other
  #graph_demo = GraphDemo2()
  #print("graph_demo.c = 'c':")
  #graph_demo.c = 'c'
  #print(graph_demo.a)
  #print(graph_demo.b)
  #print(graph_demo.d)
  
  # Causes Recursion problems (intentional) <- a and b must be preset since they are dependent on each other
  #graph_demo = GraphDemo2()
  #graph_demo.d = 'd'
  #print(graph_demo.a)
  #print(graph_demo.b)
  #print(graph_demo.c)


# checking for any residual threads lyin about
if __name__ == "__main__":
  print(threading.enumerate())




