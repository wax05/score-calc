with open("./query.txt","r",encoding="utf-8") as f:
    korean_query = []
    sql_query = []
    for line in f.readlines():
        line.rstrip()
        query_raw = line.split("\"")
        sql_query.append(query_raw[1])
        korean_query.append(query_raw[2].replace("#","").replace("\n",""))
    print(korean_query)
    print(sql_query)