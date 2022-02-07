# def solution(number):
#     sum = 0
#     for i in range(number):
#         if i % 3 == 0 or i % 5 == 0:
#             sum += i
#     return sum
#
#
# print(solution(16))

# import string
#
# s = "The quick, brown fox jumps over the lazy dog!"
#
#
# def is_pangram(s):
#     base = string.ascii_lowercase + string.
#     for i in s:
#         if i in string.
#     return False
#
#
# is_pangram("The quick, brown fox jumps over the lazy dog!")
#
# print(chr(97))
# print(chr(122))

# bus_stop = [[10, 0], [3, 5], [5, 8]]
# unzip = zip(*bus_stop)
# unzip_list = list(unzip)
#
#
# print(sum(unzip_list[1]) - sum(unzip_list[0]))

# a1 = "abc"
# a2 = "def"
# b1 = "aehrsty"
#
#
# def longest(a1, a2):
#     char = []
#     for i in a1 + a2:
#         char.append(i)
#
#     print(char)
#     char = set(char)
#     char = list(char)
#     char.sort()
#     return ''.join(char)
#
#
# print(longest(a1, a2))
# import re
#
# text = 'asd dsadas, sadsa. sadsa.das sad?sad'
# print(re.split(' |,|\.|\?', text))

# list = [1,2,2]
#
# def sumPow(list):
#     return sum(map(lambda x: x**2, list))
#
# print(sumPow(list))

# array1 = [True,  True,  True,  False,
#           True,  True,  True,  True ,
#           True,  False, True,  False,
#           True,  False, False, True ,
#           True,  True,  True,  True ,
#           False, False, True,  True ]
#
#
# def count_sheeps(sheep):
#     return sum(sheep)
#
#
# print(count_sheeps(array1))

# print(656**0.5)


# def find_next_square(sq):
#     number = int(sq**0.5)
#     if number.is_integer():
#         return (number + 1) ** 2
#     return -1
#
#
# print(find_next_square(9))
