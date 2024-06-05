import os
import sqlite3

UTF_8 = "utf-8"

QUERY_HELP = """
사용가능 키워드
    숫자: 0~100까지 사용가능합니다.
    100점초과는 자동으로 100점이상으로 바뀝니다.
    이상, 이하, 초과, 미만: 조건식
    웹프로그래밍, 파이썬프로그래밍, 알고리즘: 과목점수
    또는: OR
    그리고: AND
찾기 결과
    결과 1개: 학번, 이름
    결과 2개 이상: [(학번, 이름), (학번, 이름), ...]
"""

KOREAN_QUERY_KEYWORDS = ['이상', '이하', '초과', '미만', '그리고', '또는', '웹프로그래밍', '파이썬프로그래밍', '알고리즘']
SQL_QUERY_KEYWORDS = ['>=', '<=', '>', '<', 'AND', 'OR', 'Web', 'Python', 'Algorithm']
SQL_TABLE_KEYWORDS = SQL_QUERY_KEYWORDS[-3:]
SQL_VALUE_COMPARISON_OPERATORS = SQL_QUERY_KEYWORDS[:4]
SQL_LOGIC_OPERATORS = SQL_QUERY_KEYWORDS[4:5]


def calculate_average(scores: dict, index: int) -> float:
    total = sum(score[index] for score in scores.values())
    return total / len(scores)


def swap_list_elements(lst: list, index1: int = 0, index2: int = 1) -> list:
    lst[index1], lst[index2] = lst[index2], lst[index1]
    return lst


def validate_query_syntax(korean_query: str) -> bool:
    previous_type = ""
    logic_count = 0

    for element in korean_query.split(" "):
        if element in {"파이썬프로그래밍", "웹프로그래밍", "알고리즘"}:
            if previous_type in {"subject", ""}:
                previous_type = "subject"
                logic_count = 0
            else:
                return False
        elif element in {"이상", "이하", "초과", "미만"}:
            if previous_type in {"subject", "connective"} or logic_count < 2:
                previous_type = "logic"
                logic_count += 1
            else:
                return False
        elif element in {"그리고", "또는"}:
            if previous_type == "logic":
                previous_type = "bit_logic"
            else:
                return False
        elif element == "점수":
            if previous_type == "subject":
                previous_type = "connective"
            else:
                return False
        else:
            try:
                int(element)
                if previous_type in {"subject", "logic", "connective"} or logic_count < 2:
                    previous_type = "number"
                else:
                    return False
            except ValueError:
                return False

    return True


def convert_korean_to_sql_elements(korean_query_elements: list[str]) -> list[str]:
    start_indices = [idx for idx, elem in enumerate(korean_query_elements) if elem in SQL_TABLE_KEYWORDS]
    start_indices.sort()
    table_keyword_count = len(start_indices)
    comparison_operator_count = sum(korean_query_elements.count(op) for op in SQL_VALUE_COMPARISON_OPERATORS)

    for idx in start_indices:
        if table_keyword_count * 2 < comparison_operator_count:
            korean_query_elements[idx + 1], korean_query_elements[idx + 2] = korean_query_elements[idx + 2], korean_query_elements[idx + 1]
            korean_query_elements[idx + 3], korean_query_elements[idx + 4] = korean_query_elements[idx + 4], korean_query_elements[idx + 3]
        else:
            korean_query_elements[idx + 1], korean_query_elements[idx + 2] = korean_query_elements[idx + 2], korean_query_elements[idx + 1]

    return korean_query_elements


def convert_sql_elements_to_query(sql_query_elements: list[str]) -> str:
    base_query = "SELECT * FROM ExamScores WHERE "
    temp_table_name = ""
    is_second_comparison_operator = False

    for idx, element in sql_query_elements:
        if element in SQL_VALUE_COMPARISON_OPERATORS and is_second_comparison_operator:
            base_query += f"AND {temp_table_name} "
        elif element in SQL_TABLE_KEYWORDS:
            temp_table_name = element
            is_second_comparison_operator = False

        base_query += element + " "

        if idx == len(sql_query_elements) - 1:
            base_query = base_query.rstrip() + ";"

    return base_query


def convert_korean_to_sql_query(korean_query: str) -> str:
    if not validate_query_syntax(korean_query):
        raise ValueError("Query syntax is incorrect")

    query_elements = korean_query.split(" ")
    translated_elements = []

    for element in query_elements:
        if element in KOREAN_QUERY_KEYWORDS:
            translated_elements.append(SQL_QUERY_KEYWORDS[KOREAN_QUERY_KEYWORDS.index(element)])
        else:
            try:
                int(element)
                translated_elements.append(element)
            except ValueError:
                if len(element) > 3:
                    translated_elements.append("100")
                else:
                    translated_elements.append(element)

    sql_query_elements = convert_korean_to_sql_elements(translated_elements)
    return convert_sql_elements_to_query(sql_query_elements)


def search_by_student_number(name_index, scores):
    student_number = input("학번을 입력하세요: ")
    try:
        student_scores = scores[student_number]
        print(f"{student_number} {name_index[student_number]} 웹프로그래밍[{student_scores[0]}]점 파이썬프로그래밍[{student_scores[1]}]점 알고리즘[{student_scores[2]}]점 총점 {sum(student_scores[:2])}점")
    except KeyError:
        print("해당 학생은 존재하지 않습니다.")


def separate_grades(name_index, scores):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1][3], reverse=True)
    grade_ranges = {"A": int(len(scores) * 0.2), "B": int(len(scores) * 0.5), "C": int(len(scores) * 0.7)}

    for grade, range_limit in grade_ranges.items():
        with open(f"{grade}.txt", "w+", encoding=UTF_8) as f:
            for key, _ in sorted_scores[:range_limit]:
                f.write(f"{key} {name_index[key]}\n")

    with open("D.txt", "w+", encoding=UTF_8) as f:
        for key, _ in sorted_scores[grade_ranges["C"]:]:
            f.write(f"{key} {name_index[key]}\n")


def load_data(filename="./data.txt"):
    name_index = {}
    scores = {}

    with open(filename, "r", encoding=UTF_8) as f:
        for line in f:
            data = line.strip().split(" ")
            student_number, student_name = data[0], data[1]
            web, python, algorithm = map(int, data[2:5])
            scores[student_number] = [web, python, algorithm, web + python + algorithm]
            name_index[student_number] = student_name

    return name_index, scores


def separate_grades_by_year(name_index, scores):
    year_separated_scores = {str(year): [] for year in range(2020, 2025)}

    for student_number, student_scores in scores.items():
        year = student_number[:4]
        year_separated_scores[year].append([student_number, student_scores])

    for year in range(2020, 2025):
        year_str = str(year)
        year_separated_scores[year_str] = sorted(year_separated_scores[year_str], key=lambda x: x[1][3], reverse=True)
        write_year_separated_file(name_index, year_separated_scores, year_str)


def write_year_separated_file(name_index, year_separated_scores, year):
    with open(f"./{year}.txt", "w+", encoding=UTF_8) as f:
        top_scores = []
        lowest_scores = []
        top_score = -1
        lowest_score = -1

        for student in year_separated_scores[year]:
            if top_score == -1:
                top_score = student[1][3]
            if student[1][3] == top_score:
                top_scores.append(student)
            else:
                break

        for student in reversed(year_separated_scores[year]):
            if lowest_score == -1:
                lowest_score = student[1][3]
            if student[1][3] == lowest_score:
                lowest_scores.append(student)
            else:
                break

        for student in top_scores:
            f.write(f"1등 : {student[0]} {name_index[student[0]]} 총점 {student[1][3]}\n")
        for student in lowest_scores:
            f.write(f"꼴등 : {student[0]} {name_index[student[0]]} 총점 {student[1][3]}\n")


def main():
    name_index, scores = load_data()
    web_programming_avg = calculate_average(scores, 0)
    python_programming_avg = calculate_average(scores, 1)
    algorithm_avg = calculate_average(scores, 2)

    print(f"웹프로그래밍 평균: {web_programming_avg}")
    print(f"파이썬프로그래밍 평균: {python_programming_avg}")
    print(f"알고리즘 평균: {algorithm_avg}")

    while True:
        command = input("커맨드 종류\n1.학번으로 성적 조회\n2.조건문으로 성적 조회\n3.CSV파일로 내보내기\n-1.나가기\n커맨드를 입력해주세요: ")

        if command == "1":
            search_by_student_number(name_index, scores)
        elif command == "2":
            query_scores(name_index, scores)
        elif command == "3":
            export_to_csv()
        elif command == "-1":
            print("프로그램을 종료합니다.")
            break
        else:
            print("올바른 커맨드를 입력해주세요.")


def query_scores(name_index, scores):
    db_filename = input("데이터베이스 파일 이름을 입력해주세요 (확장자 제외): ")

    if not os.path.isdir("db"):
        os.mkdir("db")

    init_sql_table = not os.path.exists(f"./db/{db_filename}.db")
    conn = sqlite3.connect(f"./db/{db_filename}.db")
    cursor = conn.cursor()

    if init_sql_table:
        cursor.execute("CREATE TABLE ExamScores (Number INTEGER PRIMARY KEY, Name TEXT, Web INTEGER, Python INTEGER, Algorithm INTEGER);")
        for number, score in scores.items():
            cursor.execute("INSERT INTO ExamScores VALUES (?,?,?,?,?);", (number, name_index[number], score[0], score[1], score[2]))
        cursor.execute("CREATE INDEX NameIndex ON ExamScores (Name);")
        conn.commit()

    while True:
        korean_query = input("조회식을 입력해주세요...\n")
        if korean_query == "도움말":
            print(QUERY_HELP)
        elif korean_query == "나가기":
            break
        else:
            try:
                query = convert_korean_to_sql_query(korean_query)
                res = cursor.execute(query)
                results = res.fetchall()
                conn.commit()

                print("학번\t\t이름\t웹\t파이썬\t알고리즘")
                for row in results:
                    print("\t".join(map(str, row)))

                if input("CSV파일로 내보내겠습니까? (예,아니오): ") == "예":
                    csv_data = "\n".join([",".join(map(str, row)) for row in results])
                    csv_filename = input("CSV파일 이름을 입력해주세요: ")
                    with open(f"./{csv_filename}.csv", "w+", encoding=UTF_8) as f:
                        f.write(csv_data)
                    print(f"내보내기가 끝났습니다.\n{csv_filename}.csv 을 확인해주세요.")
            except (sqlite3.OperationalError, ValueError) as e:
                print(f"오류: {e}")
    cursor.close()
    conn.close()


def export_to_csv():
    filename = input("CSV파일 이름을 입력해주세요: ")
    new_data = ""

    with open("./data.txt", "r", encoding=UTF_8) as f:
        data = f.read()
        for line in data.split("\n"):
            new_data += ",".join(line.split(" ")) + "\n"

    with open(f"./{filename}.csv", "w+", encoding=UTF_8) as csv:
        csv.write(new_data)

    print(f"{filename}.csv 파일로 내보냈습니다.")


if __name__ == "__main__":
    main()
