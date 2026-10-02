# 반복 구조 안의 선택 구조와 break
n = int(input("2 이상의 정수 입력: "))
i = 2

while i < n:
    if n % i == 0:
        break
    i = i + 1

if i == n:
    print("prime")
else:
    print("composite")
