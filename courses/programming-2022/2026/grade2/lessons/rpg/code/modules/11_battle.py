class BattleManager:
    def __init__(self, game):
        self.game = game
 
    def player_normal_attack(self, monster):
        player = self.game.player
        result = DamageCalculator.calculate(
            player.total_attack,
            monster.defense,
            power=0,
            critical_chance=0.12
        )
        monster.take_damage(result['damage'])
        return result
 
    def player_skill_attack(self, monster, skill):
        player = self.game.player
        if not player.spend_mp(skill.mp_cost):
            return {'success': False, 'reason': 'MP 부족'}
        result = DamageCalculator.calculate(
            player.total_attack,
            monster.defense,
            power=skill.power,
            critical_chance=0.12 + skill.critical_bonus
        )
        monster.take_damage(result['damage'])
        result['success'] = True
        result['skill_name'] = skill.name
        return result
 
    def monster_attack(self, monster):
        player = self.game.player
        result = DamageCalculator.calculate(
            monster.attack,
            player.total_defense,
            power=0,
            critical_chance=0.05
        )
        player.hp = clamp(player.hp - result['damage'], 0, player.max_hp)
        return result
 
    def choose_skill(self):
        player = self.game.player
        for index, skill in enumerate(player.skills, start=1):
            print(f'{index}. {skill.name} (MP {skill.mp_cost}, 위력 {skill.power})')
        text = input('사용할 스킬 번호> ').strip()
        if not text.isdigit():
            return None
        index = int(text) - 1
        if 0 <= index < len(player.skills):
            return player.skills[index]
        return None
 
    def battle(self, monster):
        game = self.game
        player = game.player
        game.state = GameState.BATTLE
        print(f'⚔️ {monster.name}와 전투 시작!')
 
        while monster.is_alive() and player.is_alive():
            line()
            print(player.status_text())
            print(f'👾 {monster.name} HP 
            command = input('전투 명령 [공격/스킬/회복/도망]> ').strip()
 
            if command == '공격':
                result = self.player_normal_attack(monster)
                marker = '💥 치명타!' if result['critical'] else ''
                print(f"🗡️ {result['damage']} 피해! {marker}")
            elif command == '스킬':
                skill = self.choose_skill()
                if skill is None:
                    print('❌ 올바른 스킬을 선택하지 않았습니다.')
                    continue
                result = self.player_skill_attack(monster, skill)
                if not result.get('success'):
                    print('❌ MP가 부족합니다.')
                    continue
                marker = '💥 치명타!' if result['critical'] else ''
                print(f"🔥 {result['skill_name']}! {result['damage']} 피해! {marker}")
            elif command == '회복':
                potion = None
                for item in player.inventory.items:
                    if item.item_type == ItemType.POTION:
                        potion = item
                        break
                if potion is None:
                    print('❌ 사용할 포션이 없습니다.')
                    continue
                recovered = player.heal(potion.hp_heal, potion.mp_heal)
                player.inventory.remove(potion)
                print(f"🧪 HP +{recovered['hp_recovered']}, MP 
            elif command == '도망':
                if random.random() < 0.55:
                    print('🏃 전투에서 도망쳤습니다.')
                    game.state = GameState.EXPLORING
                    return BattleResult.ESCAPE
                print('❌ 도망에 실패했습니다!')
            else:
                print('❌ 알 수 없는 전투 명령입니다.')
                continue
 
            if not monster.is_alive():
                break
 
            enemy_result = self.monster_attack(monster)
            print(f"👾 {monster.name}의 공격! {enemy_result['damage']} 피해를 받았습니다.")
 
        if not player.is_alive():
            game.state = GameState.GAME_OVER
            return BattleResult.LOSE
 
        reward = RewardManager.give_reward(player, monster,  
        print(f"🏆 승리! EXP +{reward['exp']}, GOLD +{reward['gold']}")
        if reward['level_ups'] > 0:
            print(f'⬆️ 레벨 업! 현재 레벨 {player.level}')
        if reward['dropped_item']:
            print(f"🎁 {reward['dropped_item'].name} 획득!")
 
        quest_updates = 
        for quest in quest_updates:
            print(f'📜 퀘스트 진행: {quest.name} 
 
        game.state = GameState.EXPLORING
        return BattleResult.WIN
 
print('✅ [모듈 11] BattleManager 정의 완료')
