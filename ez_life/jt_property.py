#!/usr/bin/env python
# coding: utf-8

import copy
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
    #print("displaying graph")
    for data, node in self.data2node.items():
      print(f"{data} points to {set(n.data for n in node._edges)}")


class ClsGraphSys(dict):
  def resetDepDFS(self, cls, obj, protected_name):
    """
    Runs a DFS alrgorithm on the graph datastructure to reset all downstream dependencies to None
    parameters
      -- cls = type(obj)
      -- cls_name = type(obj).__qualname__
      -- obj: the class object that we are dealing with
      -- protected_name: the name prefixed with an underscore
    """

    """ find node of protected_name """
    node = None
    for parent in cls.__mro__[:-1]:
      parent_graph = self.get(parent.__qualname__, None)
      if parent_graph is not None:
        node = parent_graph.data2node.get(protected_name, None)
        if node is not None:
            break

    if node is None:
      return

    def recursiveReset(node):
      if (not isinstance(node, Node)) or node.was_visited:
        return
      node.was_visited = True
      if (node.data in dir(obj)) and getattr(obj, node.data) is not None: # added this here so that recursion stops when the attribute is already None such that downstream dependencies are not reset since they are assumed to be also None, or preset to some value 
        setattr(obj, node.data, None)
        [recursiveReset(n) for n in node._edges]
  
    recursiveReset(node)

    """ reseting all nodes visited to False for next iteration"""
    for parent in cls.__mro__[:-1]:
      parent_graph = self.get(parent.__qualname__, None)
      if parent_graph is not None:
        for n in parent_graph.data2node.values():
          n.was_visited = False
  
  def disp(self):
    for cls, graph in self.items():
      print(f"for cls: {cls}")
      graph.disp()


if __name__ == "__main__":
  cls_dict = ClsGraphSys()
  cls_dict['1'] = 4
  print(type(cls_dict))


class DefaultSetter:
    def __init__(self, setter):
      self.setter = setter
    def __call__(self, _func):
      if str(self.setter).lower() in "default":
        _func = _func.setter(self.defaultSetter)
      return _func
    
    @staticmethod
    def defaultSetter(obj, var):
      return var


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
        JTProperty_obj.joinClsThreads() # ensures that all class variables become available 

        cls = type(obj)
        cls_name = cls.__qualname__
        JTProperty_obj.cls_name2graph_sys[cls_name].resetDepDFS(cls, obj, JTProperty_obj.protected_name)

        setattr(obj, JTProperty_obj.protected_name, _func(obj, val))
      return wrapper
  
    def setter(self, _func):
      """
      calls setter_preprocess wrapper to alter behaviour of _func
      """
      return super().setter(self.setter_preprocess(_func))
  return ClsWrapper



class JTProperty:

  # dicts for clsWasDeclared multithreading
  cls_name2cls = {}
  cls_name2thread = {}
  cls_name2active_t = {} # stores currently active threads

  # contains scaffolds of cls graphs
  cls_name2graph = {}
  # contains actual cls graph systems
  cls_name2graph_sys = {}

  # maps the name of the classes to a list of protected variables which were defined in a class
  cls_name2protected_names = {}

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
    #check if all dependencies are a string (or a EzProperty instance <- not implemented)
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

  def addProtectedNames2ClsName(self):
    """ adding property to a dict containing the name of class in which it belongs too"""
    if self.cls_name2protected_names.get(self.cls_name, None) is None:
      self.cls_name2protected_names[self.cls_name] = [self.protected_name]
    else:
      self.cls_name2protected_names[self.cls_name].append(self.protected_name) 
    
  def initDepGraph(self):
    """ Initialises a dep graph for the class of the decorated function and/or builds edges and nodes"""
    # Create a graph if not available
    cls_graph = self.cls_name2graph.get(self.cls_name, None)
    if cls_graph is None:
      self.cls_name2graph[self.cls_name] = Graph(self.cls_name)

    # add edges for dependencies
    if self.deps is not None:
      self.cls_name2graph[self.cls_name].add(out = self.deps, into = self.protected_name)
    else: # important for inheritence
      self.cls_name2graph[self.cls_name].add(out = [], into = self.protected_name)

  def __call__(self, _func):
    self._func = _func
    self.public_name = _func.__name__
    self.protected_name = f"_{self.public_name}"

    self.cls_name = _func.__qualname__.rsplit('.', 1)[0]
    #cls = inspect._findclass(_func) <- big annoying problem: can't get cls from _func within this __call__ method, cls is not a global variable yet <- this is also why multithreading was used

    self.addProtectedNames2ClsName()
    self.initDepGraph()

    # the getter method here
    @DefaultSetter(self.setter)
    @EzProperty(self)
    @functools.wraps(_func)
    def wrapper(obj):
      self.joinClsThreads() # ensures inherited classes' nodes have been fully connected
      return self.getVar(obj)

    # perform tasks after cls is declared (run this last to reduce busy waiting load)
    self.clsWasDeclared()
    return wrapper

  def clsWasDeclared(self):
    def cls_name2Cls():
      # is a listener like this efficient? Can someone let me know please, my concern is that this listener would be considered "busy"

      # Code below was inspired by inspect.py -> _findclass() 
      cls_not_found = True
      while cls_not_found:
        cls_not_found = False
        cls = sys.modules.get(self._func.__module__)
        for name in self.cls_name.split('.'):
          if name in dir(cls):
            cls = getattr(cls, name)
          else:
            cls_not_found = True
            break

      self.cls_name2cls[self.cls_name] = cls 

      # do tasks here after cls is declared
      self.createDepGraph(cls)
    
    # we only run this block once (for the first decorated method in the class)
    if self.cls_name2thread.get(self.cls_name, None) is None:
      self.cls_name2thread[self.cls_name] = threading.Thread(target = cls_name2Cls)
      self.cls_name2thread[self.cls_name].start()

      self.cls_name2active_t[self.cls_name] = self.cls_name2thread[self.cls_name] # to denote that its running

  def createDepGraph(self, cls):
    """ ensuring that all parent threads are complete"""
    for parent in cls.__mro__[-2:0:-1]: # exclude beginning and end, and reverse the list
      parent_name = parent.__qualname__
      parent_t = self.cls_name2active_t.pop(parent_name, None)
      if parent_t is not None:
        parent_t.join()
    
    """cls_name2graph_sys initialisation and copying class parent graphs"""
    self.cls_name2graph_sys[self.cls_name] = ClsGraphSys({self.cls_name : self.cls_name2graph[self.cls_name]}) #ClsGraph inherits from dict, has method resetDepGraph

    cls_graph_sys = self.cls_name2graph_sys[self.cls_name]

    def cpParentGraphs(cls):
      for parent in cls.__bases__: # only use parents that are directly inherited
        if parent is not object: # case for no inheritence
          parent_graph = self.cls_name2graph_sys.get(parent.__qualname__) # cases where classes may not have JTProperty decorators
          if parent_graph is not None:
            cls_graph_sys.update(copy.deepcopy(parent_graph)) # make deep copies of the parent graphs to prevent effecting the parent graph
          else:
            cpParentGraphs(parent) # if a class does not have JTProperty decorators, get parent classes of this parent
    cpParentGraphs(cls)

    """connecting nodes from parent classes"""
    prot_names2del = []
    for data, node in cls_graph_sys[self.cls_name].data2node.items(): # data is the protected decorated _func name
      for parent in cls.__mro__[:-1]: # we want to go in order of how Python searches through the inherited classes excluding final object class
        parent_name = parent.__qualname__

        parent_prot_name = self.cls_name2protected_names.get(parent_name)
        if parent_prot_name is not None: # edge test case: parent may not have JTProperty Decorator inside
          if data in parent_prot_name: # check if the protected variable was defined in this parent class
            if parent is not cls: # don't need to reconnect nodes when the protected variable is inside cls
              # adding node connections
              parent_node = cls_graph_sys[parent_name].data2node[data]
              parent_node.addEdge(node._edges)
              prot_names2del.append(data)
            break # make sure to get out of the MRO loop as soon as u find the variable (cause that's just how MRO works)

    """ deleting uneccessary nodes """
    for protected_name in prot_names2del:
        del cls_graph_sys[self.cls_name].data2node[protected_name]
    
  def joinClsThreads(self):
    while len(self.cls_name2active_t) != 0:
      cls_name, active_t = self.cls_name2active_t.popitem()
      active_t.join()


if __name__ == '__main__':
  def print_assert(p, a = None):
    print(p)
    if a is not None:
      assert p.__str__() == a.__str__()


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
  print_assert(setandget.radius, '1')

  setandget.radius = 5
  print_assert(setandget.radius, '5')

  setandget.radius = 3
  print_assert(setandget.radius, '3')

  with contextlib.suppress(ValueError):
    setandget.radius = -5
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


class ParentGraphDemo:
  @JTProperty(setter = "Default")
  def a(self):
    return 'a'

class ChildGraphDemo(ParentGraphDemo):
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
  graph_demo = ChildGraphDemo()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: ChildGraphDemo
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()
  #for cls: ParentGraphDemo
  #_a points to {'_b'}


if __name__ == '__main__':
  graph_demo = ChildGraphDemo()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: ChildGraphDemo
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()
  #for cls: ParentGraphDemo
  #_a points to {'_b'}


class ParentAGraphDemo:
  @JTProperty(setter = "Default")
  def a(self):
    return 'a'

class ParentBGraphDemo(ParentAGraphDemo):
  @JTProperty(setter = "Default", deps = 'a')
  def b(self):
    return self.a + '->b'

class ParentCGraphDemo(ParentBGraphDemo):
  @JTProperty(setter = "Default")
  def c(self):
    return 'c'

class DGraphDemo(ParentCGraphDemo):
  @JTProperty(setter = "Default", deps = ['c', 'b'])
  def d(self):
    return self.b + '->d' + ' and ' + self.c + '->d'


if __name__ == '__main__':
  graph_demo = DGraphDemo()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: DGraphDemo
  #_d points to set()
  #for cls: ParentCGraphDemo
  #_c points to {'_d'}
  #for cls: ParentBGraphDemo
  #_b points to {'_d'}
  #for cls: ParentAGraphDemo
  #_a points to {'_b'}


if __name__ == '__main__':
  graph_demo = DGraphDemo()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: DGraphDemo
  #_d points to set()
  #for cls: ParentCGraphDemo
  #_c points to {'_d'}
  #for cls: ParentBGraphDemo
  #_b points to {'_d'}
  #for cls: ParentAGraphDemo
  #_a points to {'_b'}


class Branch1ADemo:
  @JTProperty(setter = "Default")
  def a(self):
    return 'a'

class Branch1BDemo(Branch1ADemo):
  @JTProperty(setter = "Default", deps = 'a')
  def b(self):
    return self.a + '->b'

class Branch2CDemo:
  @JTProperty(setter = "Default")
  def c(self):
    return 'c'

class JoinedDDemo(Branch1BDemo, Branch2CDemo):
  @JTProperty(setter = "Default", deps = ['c', 'b'])
  def d(self):
    return self.b + '->d' + ' and ' + self.c + '->d'


if __name__ == '__main__':
  graph_demo = JoinedDDemo()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: JoinedDDemo
  #_d points to set()
  #for cls: Branch1BDemo
  #_b points to {'_d'}
  #for cls: Branch1ADemo
  #_a points to {'_b'}
  #for cls: Branch2CDemo
  #_c points to {'_d'}}


if __name__ == '__main__':
  graph_demo = JoinedDDemo()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: JoinedDDemo
  #_d points to set()
  #for cls: Branch1BDemo
  #_b points to {'_d'}
  #for cls: Branch1ADemo
  #_a points to {'_b'}
  #for cls: Branch2CDemo
  #_c points to {'_d'}}


class ParentWithJT:
  @JTProperty(setter = "Default")
  def a(self):
    return 'a'

  @JTProperty(setter = "Default", deps = 'a')
  def b(self):
    return self.a + '->b'

class ParentNoJT(ParentWithJT):
  def randomMethodHere(self):
    pass

class ChildWithJT(ParentNoJT):
  @JTProperty(setter = "Default")
  def c(self):
    return 'c'

  @JTProperty(setter = "Default", deps = ['c', 'b'])
  def d(self):
    return self.b + '->d' + ' and ' + self.c + '->d'


if __name__ == '__main__':
  graph_demo = ChildWithJT()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: ChildWithJT
  #_c points to {'_d'}
  #_d points to set()
  #for cls: ParentWithJT
  #_a points to {'_b'}
  #_b points to {'_d'}


if __name__ == '__main__':
  graph_demo = ChildWithJT()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: ChildWithJT
  #_c points to {'_d'}
  #_d points to set()
  #for cls: ParentWithJT
  #_a points to {'_b'}
  #_b points to {'_d'}


class OuterClass:
  class InnerParentClass:
    @JTProperty(setter = "Default")
    def a(self):
      return 'a'

  class InnerChildClass(InnerParentClass):
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
  graph_demo = OuterClass.InnerChildClass()
  print_assert(graph_demo.d, 'a->b->d and c->d')
  graph_demo.a = 'A'
  print_assert(graph_demo.d, 'A->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: OuterClass.InnerChildClass
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()
  #for cls: OuterClass.InnerParentClass
  #_a points to {'_b'}


if __name__ == '__main__':
  graph_demo = OuterClass.InnerChildClass()
  graph_demo.d = 'a->b->d and c->d'
  graph_demo.a = 'A'
  print_assert(graph_demo._d, 'a->b->d and c->d')
  print_assert(graph_demo.d, 'a->b->d and c->d')
  JTProperty.cls_name2graph_sys[type(graph_demo).__qualname__].disp()
  #for cls: OuterClass.InnerChildClass
  #_b points to {'_d'}
  #_c points to {'_d'}
  #_d points to set()
  #for cls: OuterClass.InnerParentClass
  #_a points to {'_b'}


# checking for any residual threads lyin about
if __name__ == "__main__":
  print(threading.enumerate())
  # should look something like this:
  #[<_MainThread(MainThread, started 140206017951616)>, <Thread(Thread-2, started daemon 140205621974784)>, <Heartbeat(Thread-3, started daemon 140205613582080)>, <ParentPollerUnix(Thread-1, started daemon 140205549238016)>]




