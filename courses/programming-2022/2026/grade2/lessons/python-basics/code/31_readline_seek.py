# readline()과 seek()

f = open("sample.txt", "w", encoding="utf-8")
f.write("first\n")
f.write("second\n")
f.close()

f = open("sample.txt", "r", encoding="utf-8")

print(f.readline().strip())

f.seek(0)
print(f.read())

f.close()
