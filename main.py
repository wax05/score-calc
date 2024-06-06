import os
import sqlite3

UTF_8 = "utf-8"

query_help = """
사용가능 키워드
    숫자: 0~100까지 사용가능합니다.
    100점초과는 자동으로 100점이상으로 바뀝니다.
    이상,이하,초과,미만: 조건식
    웹프로그래밍, 파이썬프로그래밍, 알고리즘: 과목점수
    또는: OR
    그리고: AND
찾기 결과
    결과 1개: 학번, 이름
    결과 2개이상: [(학번,이름),(학번,이름),...]
"""

KOREAN_QUERY_KEYWORD = [
    "이상",
    "이하",
    "초과",
    "미만",
    "그리고",
    "또는",
    "웹프로그래밍",
    "파이썬",
    "알고리즘",
]
SQL_QUERY_KEYWORD = [">=", "<=", ">", "<", "AND", "OR", "Web", "Python", "Algorithm"]
SQL_TABLE_KEYWORD = SQL_QUERY_KEYWORD[-3:]
SQL_VALUE_COMPARISION_OPERATOR_KEYWORD = SQL_QUERY_KEYWORD[0:4]
SQL_LOGIC_OPERATOR_KEYWORD = SQL_QUERY_KEYWORD[4:5]

more = ">="  # 이상
below = "<="  # 이하
over = ">"  # 초과
under = "<"  # 미만
_and = "AND"  # 그리고
_or = "OR"  # 또는
web = "Web"  # 웹프로그래밍
python = "Python"  # 파이썬
algorithem = "Algorithem"  # 알고리즘


def calc_avg(scores: dict, idx: int) -> float:
    _sum = 0
    for score in scores:
        _sum += score[idx]
    return _sum / len(scores)


def change_index(_list: list, idx1: int = 0, idx2: int = 1) -> list:
    temp = _list[idx1]
    _list[idx1] = _list[idx2]
    _list[idx2] = temp
    return _list


def check_query_syntax(korean_query: str) -> bool:
    before_type = ""
    logic_count = 0
    for element in korean_query.split(" "):
        if "파이썬" == element or "웹프로그래밍" == element or "알고리즘" == element:
            if before_type == "subject" or not (
                before_type == "bit_logic" or before_type == ""
            ):
                return False
            before_type = "subject"
            logic_count = 0
        elif (
            element == "이상"
            or element == "이하"
            or element == "초과"
            or element == "미만"
        ):
            if before_type == "number" or logic_count < 2:
                before_type = "logic"
                logic_count += 1
            else:
                return False
        elif element == "그리고" or element == "또는":
            if not before_type == "logic":
                return False
            before_type = "bit_logic"
        elif element == "점수":
            if not before_type == "subject" or before_type == "connective":
                return False
            before_type = "connective"
        else:
            type_casting_success_index = -1
            try:
                for index in range(len(element)):
                    int(element[index])
                    type_casting_success_index = index
                if (
                    before_type == "subject"
                    or before_type == "logic"
                    or before_type == "connective"
                    or logic_count < 2
                ):
                    before_type = "number"
                else:
                    return False
            except ValueError:
                if type_casting_success_index == -1:
                    return False
                elif type_casting_success_index >= 0:
                    if (
                        before_type == "subject"
                        or before_type == "logic"
                        or before_type == "connective"
                        or logic_count < 2
                    ):
                        before_type = "number"
                else:
                    return False
    return True


def korean_context2sql_query_context(raw_sql_query_list: list[str]) -> list[str]:
    start_idx = []
    table_keyword_count = 0
    for tabe_keyward in SQL_TABLE_KEYWORD:
        for idx, sql_keyward in enumerate(raw_sql_query_list):
            if sql_keyward == tabe_keyward:
                table_keyword_count += 1
                start_idx.append(idx)

    start_idx.sort()

    comparision_operator_count = 0
    for keyword in SQL_VALUE_COMPARISION_OPERATOR_KEYWORD:
        if not raw_sql_query_list.count(keyword) == 0:
            comparision_operator_count += 1

    for idx in start_idx:
        if table_keyword_count * 2 < comparision_operator_count:
            temp = raw_sql_query_list[idx + 1]
            raw_sql_query_list[idx + 1] = raw_sql_query_list[idx + 2]
            raw_sql_query_list[idx + 2] = temp
            temp = raw_sql_query_list[idx + 3]
            raw_sql_query_list[idx + 3] = raw_sql_query_list[idx + 4]
            raw_sql_query_list[idx + 4] = temp
        else:
            temp = raw_sql_query_list[idx + 1]
            raw_sql_query_list[idx + 1] = raw_sql_query_list[idx + 2]
            raw_sql_query_list[idx + 2] = temp

    return raw_sql_query_list


def sql_query_context_list2sql_query(sql_query_context_list: list[str]) -> str:
    base_query = "SELECT * FROM ExamScores WHERE "
    temp_table_name = ""
    is_second_compraision_operator = False
    for idx, element in enumerate(sql_query_context_list):
        temp_sql_query = ""
        if (
            element in SQL_VALUE_COMPARISION_OPERATOR_KEYWORD
            and not is_second_compraision_operator
        ):
            is_second_compraision_operator = True
        elif (
            element in SQL_VALUE_COMPARISION_OPERATOR_KEYWORD
            and is_second_compraision_operator
        ):
            temp_sql_query += f"AND {temp_table_name} "
        if element in SQL_TABLE_KEYWORD:
            temp_table_name = element
            is_second_compraision_operator = False
        temp_sql_query += element + " "
        if idx == len(sql_query_context_list) - 1:
            temp_sql_query = temp_sql_query[:-1] + ";"
        base_query += temp_sql_query
    return base_query


def korean2sql_query(korean_query: str) -> str:
    if not check_query_syntax(korean_query):
        raise ValueError()
    asembly_list = []
    query_elements = korean_query.split(" ")
    for element in query_elements:
        try:
            idx = KOREAN_QUERY_KEYWORD.index(element)
            asembly_list.append(SQL_QUERY_KEYWORD[idx])
        except ValueError:
            try:
                type_casting_success_index = 0
                for idx in range(len(element)):
                    int(element[idx])
                    type_casting_success_index += 1
                if type_casting_success_index >= 3:
                    asembly_list.append("100")
                else:
                    asembly_list.append(element)
            except:
                asembly_list.append(element[0:type_casting_success_index])

    return sql_query_context_list2sql_query(
        korean_context2sql_query_context(asembly_list)
    )


def search_from_number(name_index, score):
    number = input("학번을 입력하세요 : ")
    try:
        print(
            f"{number} {name_index[number]} 웹 프로그래밍[{score[number][0]}]점 파이썬 프로그래밍[{score[number][1]}]점 알고리즘[{score[number][2]}]점 총점 {sum(score[number][0:2])}점"
        )
    except KeyError:
        print("해당 학생은 존재하지 않습니다.")


def sep_grade(name_index, score, sorted_score):
    temp_score = {}
    for key in sorted_score:
        temp_score[key] = score[key]
    score = temp_score
    A_range = int((len(score) * 0.2))
    B_range = int((len(score) * 0.5))
    C_range = int((len(score) * 0.7))
    with open("A.txt", "w+", encoding=UTF_8) as f:
        score_range = score.keys()
        for key in list(score_range)[0:A_range]:
            f.writelines(
                f"{key} {name_index[key]} {score[key][0]} {score[key][1]} {score[key][2]}\n"
            )
    with open("B.txt", "w+", encoding=UTF_8) as f:
        score_range = score.keys()
        for key in list(score_range)[A_range:B_range]:
            f.writelines(f"{key} {name_index[key]}\n")
    with open("C.txt", "w+", encoding=UTF_8) as f:
        score_range = score.keys()
        for key in list(score_range)[B_range:C_range]:
            f.writelines(f"{key} {name_index[key]}\n")
    with open("D.txt", "w+", encoding=UTF_8) as f:
        score_range = score.keys()
        for key in list(score_range)[C_range:]:
            f.writelines(f"{key} {name_index[key]}\n")
    return score


def load_data(name_index, score, filename="./data.txt"):
    with open(filename, "r", encoding=UTF_8) as f:
        lines = f.readlines()
        for line in lines:
            splited_data = line.rstrip().split(" ")
            # ScoreList index: 0=webProgramming, 1=pythonProgramming, 2=algorithms
            score[splited_data[0]] = [
                int(splited_data[2]),
                int(splited_data[3]),
                int(splited_data[4]),
            ]
            score[splited_data[0]].append(sum(score[splited_data[0]]))
            name_index[splited_data[0]] = splited_data[1]


def sep_grade_from_number(UTF_8, name_index, score):
    number_sep = {"2020": [], "2021": [], "2022": [], "2023": [], "2024": []}
    for key in score:
        if key[0:4] == "2020":
            number_sep["2020"].append([key, score[key]])
        elif key[0:4] == "2021":
            number_sep["2021"].append([key, score[key]])
        elif key[0:4] == "2022":
            number_sep["2022"].append([key, score[key]])
        elif key[0:4] == "2023":
            number_sep["2023"].append([key, score[key]])
        else:
            number_sep["2024"].append([key, score[key]])

    get_data_sum = lambda data, idx: data[1][idx]
    for year in range(2020, 2025):
        number_sep[str(year)] = sorted(
            number_sep[str(year)], key=lambda x: x[1][3], reverse=True
        )
        data_sum = [0, 0, 0]
        for data in number_sep[str(year)]:
            for i in range(3):
                data_sum[i] += get_data_sum(data, i)
        avg = []
        for i in data_sum:
            avg.append(i / len(number_sep[str(year)]))
        write_number_sep_file(UTF_8, name_index, number_sep, year, avg)


def write_number_sep_file(UTF_8, name_index, number_sep, year, avg):

    with open(f"./{year}.txt", "w+", encoding=UTF_8) as f:
        high_score_store = []
        high_score = -1
        lower_score_store = []
        lower_score = -1

        for number_score in list(number_sep[str(year)]):
            if high_score == -1:
                high_score = number_score[1][3]
                high_score_store.append(number_score)
            elif high_score == number_score[1][3]:
                high_score_store.append(number_score)
            else:
                break
        for number_score in reversed(list(number_sep[str(year)])):
            if lower_score == -1:
                lower_score = number_score[1][3]
                lower_score_store.append(number_score)
            elif lower_score == number_score[1][3]:
                lower_score_store.append(number_score)
            else:
                break

        for user in high_score_store:
            f.writelines(f"1등 : {user[0]} {name_index[user[0]]} 총점 {user[1][3]}\n")
        for user in lower_score_store:
            f.writelines(f"꼴등 : {user[0]} {name_index[user[0]]} 총점 {user[1][3]}\n")
        f.writelines(f"웹 프로그래밍 성적 평균: {avg[0]:.2f}\n")
        f.writelines(f"파이썬 프로그래밍 성적 평균: {avg[1]:.2f}\n")
        f.writelines(f"알고리즘 성적 평균: {avg[2]:.2f}\n")


def write_asc_desc(UTF_8, name_index, scores, sorted_score):
    with open("asc.txt", "w+", encoding=UTF_8) as f:
        for number in reversed(sorted_score):
            f.write(
                f"{number} {name_index[number]} {scores[number][0]} {scores[number][1]} {scores[number][2]}\n"
            )

    with open("desc.txt", "w+", encoding=UTF_8) as f:
        for number in sorted_score:
            f.write(
                f"{number} {name_index[number]} {scores[number][0]} {scores[number][1]} {scores[number][2]}\n"
            )


if __name__ == "__main__":
    name_index = {}
    scores = {}
    load_data(name_index, scores)
    web_programming_avg = calc_avg(scores.values(), 0)
    python_programming_avg = calc_avg(scores.values(), 1)
    algorithem_avg = calc_avg(scores.values(), 2)

    # sort scores
    sorted_by_number = sorted(scores.items(), key=lambda x: x[0])
    sorted_score = dict(sorted(scores.items(), key=lambda x: x[1][3], reverse=True))

    # write score
    write_asc_desc(UTF_8, name_index, scores, sorted_score)

    # sort from number
    scores = sep_grade(name_index, scores, sorted_score)

    # number file separate logic
    sep_grade_from_number(UTF_8, name_index, scores)

    while True:
        try:
            init_sql_table = False
            command = input(
                "커맨드 종류\n1.학번으로 성적 조회\n2.조건문으로 성적 조회\n3.CSV파일로 내보내기\n-1.나가기\n커맨드를 입력해주세요 : "
            )
            if command == "1":
                search_from_number(name_index, scores)
            elif command == "2":
                is_pass = False
                print(
                    "조건문은 조회만 가능합니다.\n학번기준으로 데이터 오름차순 정렬이 되어있습니다."
                )
                table_struct = """테이블 구조\n------------------------------------------------------------------\n| 학번 | 이름 | 웹프로그래밍 점수 | 파이썬프로그래밍 점수 | 알고리즘 점수 |\n------------------------------------------------------------------\n학번,이름 : String 웹프로그래밍 점수, 파이썬프로그래밍 점수, 알고리즘 점수 : Int"""
                print(table_struct)
                db_filename = input(
                    "데이터베이스 파일 이름을 입력해주세요 (확장자 제외) : "
                )
                # dir check and make dir
                if not os.path.isdir("db"):
                    os.mkdir("db")
                else:
                    file_list = os.listdir("./db")
                    for file in file_list:
                        if file == db_filename + ".db":
                            if (
                                input(
                                    "동일한 파일이 이미 존재합니다.\n연결하시겠습니까? (예,아니오) : "
                                )
                                == "예"
                            ):
                                init_sql_table = True
                                break
                            else:
                                is_pass = True

                if not is_pass:
                    conn = sqlite3.connect(f"./db/{db_filename}.db")
                    cursor = conn.cursor()
                    sql_running = True
                    on_error = False

                    # table init
                    if not init_sql_table:
                        cursor.execute(
                            "CREATE TABLE ExamScores (Number INTEGER PRIMARY KEY, Name TEXT, Web INTEGER, Python INTEGER, Algorithm INTEGER);"
                        )
                        for number, scores in sorted_by_number:
                            cursor.execute(
                                "INSERT INTO ExamScores VALUES (?,?,?,?,?);",
                                (
                                    number,
                                    name_index[number],
                                    scores[0],
                                    scores[1],
                                    scores[2],
                                ),
                            )
                        cursor.execute("CREATE INDEX NameIndex ON ExamScores (Name);")
                        conn.commit()

                    loop_count = 0
                    while True:
                        korean_query = ""
                        if loop_count == 0:
                            korean_query = input(
                                '조회식을 입력해주세요.(학번과 이름이 결과로 나옵니다)\n예시 : 파이썬 20 이상 50 미만 그리고 웹프로그래밍 20 이상 또는 알고리즘 40 미만\n검색을 종료하시려면 "나가기"를 입력해주세요.\n문법 도움말을 보려면 "도움말"을 입력하세요.\n'
                            )
                            if korean_query == "도움말":
                                print(query_help)
                            elif korean_query == "나가기":
                                cursor.close()
                                conn.close()
                                break
                            else:
                                try:
                                    query = korean2sql_query(korean_query)
                                    print(query)
                                    res = cursor.execute(query)
                                    datas = res.fetchall()
                                    conn.commit()
                                    print(
                                        korean_query
                                        + " 의 검색결과입니다. ({}개)".format(
                                            len(datas)
                                        )
                                    )
                                    print("학번\t\t이름\t웹\t파이썬\t알고리즘")
                                    for row in datas:
                                        for column in row:
                                            print(column, end="\t")
                                        print()
                                    if (
                                        input("CSV파일로 내보내겠습니까? (예,아니오): ")
                                        == "예"
                                    ):
                                        csv_data = ""
                                        for row in datas:
                                            for idx, column in enumerate(row):
                                                end = ","
                                                if idx == 4:
                                                    end += "\n"
                                                csv_data += str(column) + end
                                        csv_filename = input(
                                            "CSV파일 이름을 입력해주세요: "
                                        )
                                        with open(
                                            f"./{csv_filename}.csv",
                                            "w+",
                                            encoding=UTF_8,
                                        ) as f:
                                            f.write(csv_data)
                                        print(
                                            f"내보내기가 끝났습니다.\n{csv_filename}.csv 을 확인해주세요."
                                        )
                                except sqlite3.OperationalError as e:
                                    print("\n결과가 존재하지 않습니다\n")
                                except ValueError:
                                    print("문법에 맞지 않습니다.")
                                except Exception as e:
                                    print(e)
            elif command == "3":
                filename = input("CSV파일 이름을 입력해주세요: ")
                newdata = ""

                with open("./data.txt", "r", encoding="utf-8") as f:
                    data = f.read()
                    for line in data.split("\n"):
                        datas = line.split(" ")
                        for idx, column_data in enumerate(datas):
                            if not idx == len(datas) - 1:
                                newdata += column_data + ","
                            else:
                                newdata += column_data + "\n"

                with open(f"./{filename}.csv", "w+", encoding="utf-8") as csv:
                    csv.write(newdata)

            elif command == "-1":
                print("프로그램을 종료합니다.")
                break
            else:
                print("올바른 커맨드를 입력해주세요.")
        except Exception as e:
            print(e)
