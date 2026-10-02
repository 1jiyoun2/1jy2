# 반복 구조
# 정수를 2진수 비트 리스트로 바꾸는 과정

number = int(input("0보다 큰 정수를 입력하세요: "))
bits = []
n = number

while n > 0:
    bits.append(n % 2)
    n = n // 2

bits.reverse()

print(bits)
