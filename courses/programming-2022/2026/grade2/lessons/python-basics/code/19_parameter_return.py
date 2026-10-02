# 매개변수와 반환값
def even_sum(n):
    total = 0

    for value in range(0, n + 1, 2):
        total = total + value

    return total

print(even_sum(10))
