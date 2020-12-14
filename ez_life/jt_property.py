#!/usr/bin/env python
# coding: utf-8

import functools


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
        protected_name = f"_{_func.__name__}"
        JTProperty_obj.cls_name2graph[JTProperty_obj.cls_name].resetDepDFS(obj, protected_name)
        setattr(obj, protected_name, _func(obj, val))
      return wrapper
  
    def setter(self, _func):
      """
      calls setter_preprocess wrapper to alter behaviour of _func
      """
      return super().setter(self.setter_preprocess(_func))
  return ClsWrapper


class JTProperty:
  # dict of class names (str) that have been decorated with JTProperty
  cls_name2graph = {}
  def __init__(self, setter = False, deps = None):
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

  def getVar(self, _func, obj, protected_name, public_name):
    # if self._name is not available atm or it is set to None
    if (protected_name not in dir(obj)) or (getattr(obj, protected_name) is None):
      if (not(self.setter)):
        setattr(obj, protected_name, _func(obj)) 
      else:
        # call setter method obj.name with the return value of the property function, this effectively sets obj._name
        setattr(obj, public_name, _func(obj)) 
    return getattr(obj, protected_name)

  def createDepGraph(self, cls_name, protected_name):
    cls_graph = self.cls_name2graph.get(cls_name, None)
    if cls_graph is None:
      self.cls_name2graph[cls_name] = Graph(cls_name)

    if self.deps is not None:
      self.cls_name2graph[cls_name].add(out = self.deps, into = protected_name)
      #self.cls_name2graph[cls_name].disp()

  def __call__(self, _func):
    public_name = _func.__name__
    protected_name = f"_{public_name}"


    self.cls_name = _func.__qualname__.rsplit('.', 1)[0]
    #_func_cls = inspect._findclass(_func) <- big annoying problem: can't get cls from _func within this __call__ method, cls is not a global variable yet

    self.createDepGraph(self.cls_name, protected_name)

    # the getter method here
    @EzProperty(self)
    @functools.wraps(_func)
    def wrapper(obj):
      #might need something here to connect nodes with inherited classes
      return self.getVar(_func, obj, protected_name, public_name)

    return wrapper


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


class GraphDemo:
  @JTProperty(setter = True)
  def a(self):
    return 'a'

  @a.setter
  def a(self, value):
    return value

  @JTProperty(setter = True, deps = 'a')
  def b(self):
    return self.a + '->b'

  @b.setter
  def b(self, value):
    return value
  
  @JTProperty(setter = True)
  def c(self):
    return 'c'

  @c.setter
  def c(self, value):
    return value
  
  @JTProperty(setter = True, deps = ['c', 'b'])
  def d(self):
    return self.b + '->d' + ' and ' + self.c + '->d'
  
  @d.setter
  def d(self, value):
    return value


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
  @JTProperty(setter = True, deps = ['b', 'd'])
  def a(self):
    return self.b + '->a and ' + self.d + '->a'

  @a.setter
  def a(self, value):
    return value

  @JTProperty(setter = True, deps = 'a')
  def b(self):
    return self.a + '->b'

  @b.setter
  def b(self, value):
    return value
  
  @JTProperty(setter = True, deps = 'b')
  def c(self):
    return self.b + '->c'

  @c.setter
  def c(self, value):
    return value
  
  @JTProperty(setter = True, deps = ['c'])
  def d(self):
    return self.c + '->d'
  
  @d.setter
  def d(self, value):
    return value


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




