# 모듈 14 - 게임 반복 실행

def run(self):
    print('🏰 파이썬 텍스트 RPG에 오신 것을 환영합니다!')
    self.show_help()

    while True:
        if self.state == GameState.GAME_OVER:
            print('☠️ GAME OVER')
            break

        if self.state == GameState.CLEAR:
            print('🎉 검은 용을 쓰러뜨렸습니다! GAME CLEAR!')
            break

        self.render()
        text = input('\n명령> ')
        command = CommandParser.parse(text)
        should_continue = self.process_command(command)

        if not should_continue:
            break
