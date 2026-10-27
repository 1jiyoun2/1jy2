# 모듈 12 - 저장 파일 불러오기 중 예외 처리

file_name = file_name or SaveManager.SAVE_FILE

try:
    with open(file_name, 'r', encoding='utf-8') as file:
        data = json.load(file)
except FileNotFoundError:
    return False
