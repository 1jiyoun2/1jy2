# 모듈 14 - 명령에 따른 기능 분기

def process_command(self, command):
    action = command.action
    target = command.target

    if action == '이동':
        self.move_player(target)
    elif action == '전투':
        self.start_battle()
    elif action == '줍기':
        self.pick_up_item()
    elif action == '대화':
        self.talk()
    elif action == '상태':
        print(self.player.status_text())
    elif action == '인벤토리':
        self.player.inventory.list_items()
    elif action == '장착':
        self.equip_item(target)
    elif action == '사용':
        self.use_item(target)
    elif action == '퀘스트':
        self.quest_manager.show_quests(self.player)
    elif action == '저장':
        file_name = SaveManager.save(self)
        print(f'💾 저장 완료: {file_name}')
    elif action == '불러오기':
        if SaveManager.load(self):
            print('📂 저장 데이터를 불러왔습니다.')
        else:
            print('❌ 저장 파일이 없습니다.')
    elif action == '도움말':
        self.show_help()
    elif action == '종료':
        print('👋 게임을 종료합니다.')
        return False
    elif action == '':
        pass
    else:
        print("❌ 알 수 없는 명령입니다. '도움말'을 입력해 보세요.")

    return True
