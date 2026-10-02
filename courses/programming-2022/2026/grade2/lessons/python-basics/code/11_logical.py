# 논리 연산
n = int(input("정수 입력: "))

print(n % 2 == 0)
print(n % 3 == 0)
print((n % 2 == 0) and (n % 3 == 0))
print((n % 2 == 0) or (n % 3 == 0))
print(not (n % 2 == 0))
