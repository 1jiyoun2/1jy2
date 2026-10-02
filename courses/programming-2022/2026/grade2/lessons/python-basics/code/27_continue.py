# continue: 이번 반복의 남은 부분을 건너뛰기

n = int(input("정수 입력: "))

for i in range(1, n + 1):
    if i % 3 == 0:
        continue

    print(i, end=" ")
