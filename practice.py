nums = [-1,1,0,-3,3]
n = len(nums)
result = [1] * n
left = 1
for i in range(n):
    result[i] = left
    left *= nums[i]

right = 1
for i in range(n - 1, -1, -1):
    result[i] *= right
    right *= nums[i]

print(result)


"""
nums = [1,2,3,4]
n = len(nums)
result = [0]*n
left = 1
for i,num in enumerate(nums):
    if i == 0:
        result[i] = 0
        left = num
    else:
        result[i] = left
        left *= num
right = 0
for i,num in enumerate(reversed(nums)):
    if i==0:
        right = num
        print(result)
    elif result[-i-1] == 0 and i==n-1:
        result[-i-1] = right
    else:
        result[-i-1] *= right
        print(result)
        right *= num
print(result)
"""