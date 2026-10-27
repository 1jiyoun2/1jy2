# 파일 입출력

f = open("새파일.txt", "w")
f.write("새 파일이 만들어졌습니다.")
f.close()

f = open("새파일.txt", "r")
print(f.read())
f.close()
