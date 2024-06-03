def check_query_syntax(korean_query:str)->bool:
    before_type = ""
    logic_count = 0
    for element in korean_query.split(" "):
        if "파이썬" == element or "웹프로그래밍" == element or "알고리즘" == element:
            if before_type == "subject" or not (before_type == "bit_logic" or before_type == ""):
                return False
            before_type = "subject"
            logic_count = 0
        elif element == "이상" or element == "이하" or element == "초과" or element == "미만":
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
                if before_type == "subject" or before_type == "logic" or before_type == "connective" or logic_count < 2:
                    before_type = "number"
                else:
                    return False
            except ValueError:
                if type_casting_success_index == -1:
                    return False
                elif type_casting_success_index >= 0:
                    if before_type == "subject" or before_type == "logic" or before_type == "connective" or logic_count < 2:
                        before_type = "number"    
                else:
                    return False
    return True

def change_index(_list:list,idx1:int=0,idx2:int=1)->list:
    temp = _list[idx1]
    _list[idx1] = _list[idx2]
    _list[idx2] = temp
    return _list

SQL_QUERY_KEYWORD = ['>=', '<=', '>', '<', 'AND', 'OR', 'Web', 'Python', 'Algorithem']
SQL_FIND_REV_INDEX_KEYWORD = SQL_QUERY_KEYWORD[-3:]
SQL_VALUE_COMPARISION_KEYWORD = SQL_QUERY_KEYWORD[0:3]
def korean_context2sql_query_context(raw_sql_query_list:list[str])->list[str]:
    start_idx = []
    table_keyword_count = 0
    for find_rev_keyward in SQL_FIND_REV_INDEX_KEYWORD:
        for idx,sql_keyward in enumerate(raw_sql_query_list):
            if sql_keyward == find_rev_keyward:
                start_idx.append(idx)
    
    start_idx.sort()
    
    comparision_operator_count = 0
    for keyword in SQL_VALUE_COMPARISION_KEYWORD:
        if not raw_sql_query_list.count(keyword) == 0:
            comparision_operator_count += 1



    for idx in start_idx:
        if table_keyword_count*2 < comparision_operator_count:
            temp = raw_sql_query_list[idx+1]
            raw_sql_query_list[idx+1] = raw_sql_query_list[idx+2]
            raw_sql_query_list[idx+2] = temp
            temp = raw_sql_query_list[idx+3]
            raw_sql_query_list[idx+3] = raw_sql_query_list[idx+4]
            raw_sql_query_list[idx+4] = temp
        else:
            temp = raw_sql_query_list[idx+1]
            raw_sql_query_list[idx+1] = raw_sql_query_list[idx+2]
            raw_sql_query_list[idx+2] = temp
    return raw_sql_query_list


a = ['Python', '20', '>=', '50', '<', 'OR', 'Algorithem', '20', '>=', '50', '<']

print(check_query_syntax("파이썬 점수 20점 이상 50점 미만 그리고 웹프로그래밍 점수 20점 이상 또는 알고리즘 점수 40점 미만"))
print(korean_context2sql_query_context(a))