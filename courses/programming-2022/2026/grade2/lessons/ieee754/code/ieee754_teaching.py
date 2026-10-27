# IEEE 754 단정도(32비트) 변환 - 수업용 단계별 구현
#
# 이 코드는 IEEE 754 변환의 유일한 정답이나 범용 변환기가 아닙니다.
# 수업에서 '10진수 실수 → 2진수 → 정규화 → 지수부 → 가수부 → 32비트 결합'
# 흐름을 단계별로 확인하기 위해 구성한 교육용 코드입니다.
#
# 수업에서 사용하는 전제 조건
# - 0보다 크고 16보다 작은 양의 실수
# - 소수 부분이 2진수로 유한하게 표현되는 값
# - 정규화 후 가수 후보가 23비트를 넘지 않는 값
# - 음수, 0, 16 이상, 무한 반복 소수, 반올림이 필요한 경우는 다루지 않음


# 1. 입력 처리
sign_bit = "0"

while True:
    try:
        value = float(input("입력 : "))

        if value >= 16 or value <= 0:
            print("다시 입력하세요.")
        else:
            sign_bit = "0"
            break

    except ValueError:
        print("숫자를 입력하세요.")

print("부호 비트:", sign_bit)
print("입력한 값:", value)


# 2. 정수 부분의 2진수 변환
# 정수 부분을 2로 계속 나눈 나머지를 거꾸로 배열한다.
int_bits = []
int_part = int(value)
n = int_part

if n == 0:
    int_bits = [0]
else:
    while n > 0:
        int_bits.append(n % 2)
        n = n // 2

    int_bits.reverse()

print("정수 부분:", int_part)
print("정수 부분의 비트:", int_bits)


# 3. 소수 부분의 2진수 변환
# 소수 부분에 2를 반복해서 곱하며 정수 부분으로 나온 0 또는 1을 저장한다.
frac_bits = []
frac_part = value - int_part
frac = frac_part

if frac == 0:
    frac_bits = [0]
else:
    while frac != 0:
        frac = frac * 2

        if frac >= 1:
            frac_bits.append(1)
            frac = frac - 1
        else:
            frac_bits.append(0)

print("소수 부분:", frac_part)
print("소수 부분의 비트:", frac_bits)

binary_text = ""

for bit in int_bits:
    binary_text = binary_text + str(bit)

binary_text = binary_text + "."

for bit in frac_bits:
    binary_text = binary_text + str(bit)

print("최종 연결된 2진수 :", binary_text)


# 4. 정규화 및 실제 지수 계산
# 처음 등장하는 1을 기준으로 1.xxxxx × 2^n 형태를 만든다.
normalized_bits = []
first_one = -1

for i in range(len(int_bits)):
    if int_bits[i] == 1:
        first_one = i
        break

if first_one != -1:
    # 정수 부분에 1이 있는 경우
    real_exp = len(int_bits) - first_one - 1

    # 맨 앞의 1은 숨은 비트로 보고 제외한다.
    for i in range(first_one + 1, len(int_bits)):
        normalized_bits.append(int_bits[i])

    for i in range(len(frac_bits)):
        normalized_bits.append(frac_bits[i])

else:
    # 1보다 작은 수처럼 정수 부분에서 1을 찾지 못한 경우
    first_one = -1

    for i in range(len(frac_bits)):
        if frac_bits[i] == 1:
            first_one = i
            break

    real_exp = -(first_one + 1)

    # 처음 찾은 1 다음 비트부터 가수 후보로 저장한다.
    for i in range(first_one + 1, len(frac_bits)):
        normalized_bits.append(frac_bits[i])

normalized_text = "1."

if len(normalized_bits) == 0:
    normalized_text = normalized_text + "0"
else:
    for bit in normalized_bits:
        normalized_text = normalized_text + str(bit)

normalized_text = normalized_text + " × 2^" + str(real_exp)

print("정규화 결과:", normalized_text)
print("실제 지수:", real_exp)
print("정규화 후 가수 후보:", normalized_bits)


# 5. 지수부 생성
# IEEE 754 단정도에서는 실제 지수에 bias 127을 더해 저장 지수를 만든다.
exponent_bits = []
stored_exp = real_exp + 127
n = stored_exp

if n == 0:
    exponent_bits = [0]
else:
    while n > 0:
        exponent_bits.append(n % 2)
        n = n // 2

    exponent_bits.reverse()

# 지수부가 8비트가 되도록 앞쪽에 0을 채운다.
while len(exponent_bits) < 8:
    exponent_bits = [0] + exponent_bits

print("저장 지수:", stored_exp)
print("지수부:", exponent_bits)
print("지수부 비트 수:", len(exponent_bits))


# 6. 가수부 생성
# 정규화 과정에서 만든 가수 후보 뒤에 0을 채워 23비트로 만든다.
mantissa_bits = []

for bit in normalized_bits:
    mantissa_bits.append(bit)

while len(mantissa_bits) < 23:
    mantissa_bits.append(0)

print("가수부:", mantissa_bits)
print("가수부 비트 수:", len(mantissa_bits))


# 7. 최종 32비트 결합
# 부호 1비트 + 지수부 8비트 + 가수부 23비트를 순서대로 연결한다.
ieee754 = sign_bit

for i in exponent_bits:
    ieee754 = ieee754 + str(i)

for i in mantissa_bits:
    ieee754 = ieee754 + str(i)

print("IEEE 754:", ieee754)
print("전체 비트 수:", len(ieee754))

for data in ieee754:
    print(data, end=" ")
