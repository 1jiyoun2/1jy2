class Game:
    def __init__(self, player_name='용사'):
        self.player = Player(player_name)
        self.state = GameState.EXPLORING
        self.flags: Set[str] = set()
        self.item_catalog = build_item_catalog()
        self.monster_templates = build_monster_catalog()
        self.quest_catalog = build_quest_catalog()
        self.npc_catalog = build_npc_catalog()
        self.world = build_world()
        self.quest_manager = 
        self.event_manager = EventManager()
        self.battle_manager = BattleManager(self)
        self._register_events()
        self.player.inventory.add(self.item_catalog['wood_sword'])
        self.player.inventory.add(self.item_catalog['small_potion'])
        self.player.equip(self.item_catalog['wood_sword'])
 
    def _register_events(self):
        def welcome_condition(game):
            return 'welcomed' not in game.flags
        def welcome_action(game):
            print('🔔 장로가 당신을 바라봅니다.')
            print("💡 '대화' 명령으로 장로와 이야기해 보세요.")
            game.flags.add('welcomed')
        def forest_condition(game):
            return 'forest_seen' not in game.flags
        def forest_action(game):
            print('🌲 숲 어딘가에서 늑대 울음소리가 들립니다.')
            game.flags.add('forest_seen')
        def ruins_condition(game):
            return game.player.level >= 2
        def ruins_action(game):
            print('🗿 유적의 문양이 플레이어의 힘에 반응합니다.')
            game.flags.add('ruins_awakened')
        def gate_condition(game):
            has_key = game.player.inventory.find_by_id('ancient_key') 
            return has_key and 'gate_open' not in game.flags
        def gate_action(game):
            print('🗝️ 고대의 열쇠가 빛나며 봉인이 풀립니다!')
            game.flags.add('gate_open')
        def boss_condition(game):
            return 'boss_seen' not in game.flags
        def boss_action(game):
            print('🐉 검은 용: 감히 여기까지 오다니!')
            game.flags.add('boss_seen')
        events = [
            GameEvent('welcome_event', '첫 시작 안내', 
            GameEvent('forest_warning', '숲 경고', forest_condition, 
            GameEvent('ruins_event', '유적 각성', ruins_condition, 
            GameEvent('gate_event', '봉인 해제', gate_condition, 
            GameEvent('boss_event', '보스 등장', boss_condition, 
        ]
        for event in events:
            self.event_manager.register(event)
 
    def clone_monster(self, monster_id):
        t = self.monster_templates[monster_id]
        return Monster(t.id, t.name, t.max_hp, t.max_hp, t.attack, t.defense, t.exp_reward, t.gold_reward, t.drop_item_id)
 
    def render(self):
        room = self.world.current_room
        line()
        print(f'📍 {room.name}')
        print(room.description)
        print(self.player.status_text())
        exits = ', '.join(direction.value for direction in 
        print(f"🚪 이동 가능 방향: {exits or '없음'}")
        if room.monster_ids:
            names = [self.monster_templates[mid].name for 
            print('👾 몬스터:', ', '.join(names))
        if room.item_ids:
            names = [self.item_catalog[iid].name for iid in 
            print('✨ 바닥 아이템:', ', '.join(names))
        if room.npc_id:
            print(f'🧑 NPC: {self.npc_catalog[room.npc_id].name}')
        self.event_manager.trigger_room_events(self, room)
 
    def show_help(self):
        help_lines = [
            '[탐험 명령]',
            '  이동 북 / 이동 남 / 이동 동 / 이동 서',
            '  전투', '  줍기', '  대화', '  상태', '  인벤토리',
            '  장착 아이템이름', '  사용 아이템이름', '  퀘스트',
            '  저장', '  불러오기', '  도움말', '  종료'
        ]
        print('\n'.join(help_lines))
 
    def move_player(self, target):
        direction = DIRECTION_ALIASES.get(target)
        if direction is None:
            print('❌ 방향은 북/남/동/서 중 하나를 입력하세요.')
            return
        if self.world.current_room_id == 'sealed_gate' and direction 
            print('🔒 문이 봉인되어 있습니다. 열쇠가 필요합니다.')
            return
        success = self.world.move(direction)
        if success:
            print(f'🚶 {direction.value}쪽으로 이동했습니다.')
        else:
            print('❌ 그 방향으로는 이동할 수 없습니다.')
 
    def pick_up_item(self):
        room = self.world.current_room
        if not room.item_ids:
            print('❌ 주울 아이템이 없습니다.')
            return
        item_id = room.item_ids[0]
        item = self.item_catalog[item_id]
        if self.player.inventory.add(item):
            room.item_ids.remove(item_id)
            print(f'✨ {item.name}을(를) 주웠습니다.')
        else:
            print('❌ 인벤토리가 가득 찼습니다.')
 
    def talk(self):
        room = self.world.current_room
        if not room.npc_id:
            print('❌ 대화할 사람이 없습니다.')
            return
        npc = self.npc_catalog[room.npc_id]
        self.quest_manager.talk_to_npc(self, npc)
 
    def use_item(self, item_name):
        if not item_name:
            print('사용할 아이템 이름을 입력하세요.')
            return
        item = self.player.inventory.find_by_name(item_name)
        if item is None:
            print('❌ 해당 아이템이 없습니다.')
            return
        if item.item_type != ItemType.POTION:
            print('❌ 지금 사용할 수 있는 아이템이 아닙니다.')
            return
        result = self.player.heal(item.hp_heal, item.mp_heal)
        self.player.inventory.remove(item)
        print(f"🧪 {item.name} 사용: HP 
 
    def equip_item(self, item_name):
        if not item_name:
            print('장착할 아이템 이름을 입력하세요.')
            return
        item = self.player.inventory.find_by_name(item_name)
        if item is None:
            print('❌ 해당 아이템이 없습니다.')
            return
        if self.player.equip(item):
            print(f'🛡️ {item.name} 장착 완료!')
        else:
            print('❌ 장착 가능한 아이템이 아닙니다.')
 
    def start_battle(self):
        room = self.world.current_room
        if not room.monster_ids:
            print('❌ 이곳에는 싸울 몬스터가 없습니다.')
            return
        monster_id = room.monster_ids[0]
        monster = self.clone_monster(monster_id)
        result = self.battle_manager.battle(monster)
        if result == BattleResult.WIN:
            if monster_id == 'dragon':
                self.state = GameState.CLEAR
                return
            print('⏳ 같은 종류의 몬스터가 다시 나타날 수 있습니다.')
        elif result == BattleResult.LOSE:
            self.state = GameState.GAME_OVER
 
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
 
print('✅ [모듈 14] Game 정의 완료')
