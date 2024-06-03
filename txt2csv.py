newdata = ""

with open("./data.txt","r", encoding="utf-8")as f:
    data = f.read()
    for line in data.split("\n"):
        rows = line.split(" ")
        for idx, column_data in enumerate(rows):
            if not idx == len(rows)-1:
                newdata += column_data + ","
            else:
                newdata += column_data + "\n"

with open("./data.csv", "w+",encoding="utf-8") as csv:
    csv.write(newdata)

