# 간단한 CSV 저장과 읽기
f = open("scores.csv", "w", encoding="utf-8")
f.write("name,score\n")
f.write("A,90\n")
f.write("B,85\n")
f.close()

f = open("scores.csv", "r", encoding="utf-8")
rows = f.read().split("\n")
f.close()

for row in rows:
    if row != "":
        print(row.split(","))
