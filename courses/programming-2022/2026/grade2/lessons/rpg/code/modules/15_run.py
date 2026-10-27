player_name = input('플레이어 이름을 입력하세요> ').strip()
if player_name == '':
    player_name = '용사'
game = Game(player_name)
game.run()
