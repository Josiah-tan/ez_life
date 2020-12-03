
#================================================================
#
#   File name   : test_param2attr.py
#   Author      : Josiah Tan
#   Created date: 28/11/2020
#   Description : testing param2attr module from ez_life
#
#================================================================

#================================================================

from ez_life import Param2attr

if __name__ == "__main__":
	class Foo:
		@Param2attr(exclude = 'param4')
		def __init__(self, param1 = None, param2 = None, param3 = None, param4 = None):
			pass

	foo = Foo(param1 = "john", param2 = "hog", param3 = "sam", param4 = "dob")
	print(dir(foo)[-4:])
