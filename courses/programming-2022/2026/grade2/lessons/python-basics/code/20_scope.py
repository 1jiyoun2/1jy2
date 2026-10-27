# 지역 변수와 전역 변수
s = 0

def add_to_sum(n):
    global s
    k = 0

    while k < n:
        k = k + 1
        s = s + k

add_to_sum(3)
print(s)
