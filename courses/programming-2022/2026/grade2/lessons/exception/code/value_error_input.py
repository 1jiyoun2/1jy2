# IEEE 754 수업 코드에서 사용한 ValueError 처리

while True:
    try:
        value = float(input("입력 : "))

        if value >= 16 or value <= 0:
            print("다시 입력하세요.")
        else:
            break

    except ValueError:
        print("숫자를 입력하세요.")
