# 클래스 코드를 읽기 위한 최소 예제

class Player:
    def __init__(self, name):
        self.name = name
        self.hp = 100

    def show_status(self):
        print(self.name, self.hp)


player = Player("용사")
player.show_status()
