# 추가 모드(a)
f = open("memo.txt", "w", encoding="utf-8")
f.write("첫 번째 줄\n")
f.close()

f = open("memo.txt", "a", encoding="utf-8")
f.write("두 번째 줄\n")
f.close()

f = open("memo.txt", "r", encoding="utf-8")
print(f.read())
f.close()
