# 함수 · 매개변수 · 반환값
# 텍스트 RPG에서 사용하는 공통 함수

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


hp = 120
hp = clamp(hp, 0, 100)

print(hp)
