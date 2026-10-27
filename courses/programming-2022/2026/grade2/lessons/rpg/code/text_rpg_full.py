# 텍스트 RPG 수업용 코드
# 모듈별 학습 흐름을 한 파일로 연결한 전체 코드입니다.
# 수업을 위해 구성된 코드이며 유일한 정답이나 최적해를 의미하지 않습니다.

# ===== 모듈 01 · 라이브러리와 공통 도구 =====
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict, Callable, Any, Set
 
random.seed(7)  #수업 결과 재현 위한 난수 시드 고정
 
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))
 
def line():
    print('-' * 72)
 
print('✅ [모듈 1] 라이브러리 로드 완료')

# ===== 모듈 02 · 정해진 값 =====
class Direction(Enum):
    NORTH = '북'
    SOUTH = '남'
    EAST = '동'
    WEST = '서'
 
class ItemType(Enum):
    WEAPON = auto()
    ARMOR = auto()
    POTION = auto()
    KEY = auto()
    MATERIAL = auto()
 
class GameState(Enum):
    EXPLORING = auto()
    BATTLE = auto()
    GAME_OVER = auto()
    CLEAR = auto()
 
class BattleResult(Enum):
    WIN = auto()
    LOSE = auto()
    ESCAPE = auto()
 
class QuestStatus(Enum):
    LOCKED = auto()
    AVAILABLE = auto()
    ACTIVE = auto()
    COMPLETED = auto()
 
DIRECTION_ALIASES = {
    '북': Direction.NORTH, '남': Direction.SOUTH,
    '동': Direction.EAST, '서': Direction.WEST,
    'n': Direction.NORTH, 's': Direction.SOUTH,
    'e': Direction.EAST, 'w': Direction.WEST,
}
 
print('✅ [모듈 2] Enum 정의 완료')

# ===== 모듈 03 · 게임 데이터 모델 =====
@dataclass
class Item:
    id: str
    name: str
    item_type: ItemType
    description: str
    atk_bonus: int = 0
    def_bonus: int = 0
    hp_heal: int = 0
    mp_heal: int = 0
    price: int = 0
 
@dataclass
class Skill:
    id: str
    name: str
    mp_cost: int
    power: int
    description: str
    critical_bonus: float = 0.0
 
@dataclass
class Monster:
    id: str
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    exp_reward: int
    gold_reward: int
    drop_item_id: Optional[str] = None
 
    def is_alive(self):
        return self.hp > 0
 
    def take_damage(self, damage):
        self.hp = clamp(self.hp - damage, 0, self.max_hp)
        return self.hp
 
@dataclass
class Quest:
    id: str
    name: str
    description: str
    target_monster_id: str
    required_count: int
    reward_gold: int
    reward_item_id: Optional[str] = None
    status: QuestStatus = QuestStatus.AVAILABLE
    progress: int = 0
 
    def add_progress(self, monster_id):
        if self.status != QuestStatus.ACTIVE:
            return False
        if monster_id != self.target_monster_id:
            return False
        self.progress += 1
        if self.progress >= self.required_count:
            self.status = QuestStatus.COMPLETED
        return True
 
print('✅ [모듈 3] 데이터 모델 정의 완료')

# ===== 모듈 04 · 인벤토리 =====
class Inventory:
    def __init__(self, capacity=12):
        self.items: List[Item] = []
        self.capacity = capacity
 
    def add(self, item):
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True
 
    def remove(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False
 
    def find_by_name(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None
 
    def find_by_id(self, item_id):
        for item in self.items:
            if item.id == item_id:
                return item
        return None
 
    def count_type(self, item_type):
        count = 0
        for item in self.items:
            if item.item_type == item_type:
                count += 1
        return count
 
    def list_items(self):
        if not self.items:
            print('🎒 인벤토리가 비어 있습니다.')
            return
        print(f'🎒 인벤토리 ({len(self.items)}/{self.capacity})')
        for index, item in enumerate(self.items, start=1):
            print(f'  {index}. {item.name} - {item.description}')
 
print('✅ [모듈 4] Inventory 정의 완료')

# ===== 모듈 05 · 플레이어 =====
class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.exp = 0
        self.hp = 100
        self.max_hp = 100
        self.mp = 50
        self.max_mp = 50
        self.base_attack = 15
        self.base_defense = 5
        self.gold = 50
        self.inventory = Inventory(capacity=12)
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor: Optional[Item] = None
        self.skills: List[Skill] = [
            Skill('skill_fire', '파이어볼', 15, 35, '강한 불꽃 공격', 0.10),
            Skill('skill_slash', '강타', 8, 22, '집중해서 강하게 공격', 0.05),
        ]
        self.quest_ids: List[str] = []
 
    @property
    def next_level_exp(self):
        return int(100 * math.pow(self.level, 1.5))
 
    @property
    def total_attack(self):
        bonus = self.equipped_weapon.atk_bonus if self.equipped_weapon else 0
        return self.base_attack + bonus
 
    @property
    def total_defense(self):
        bonus = self.equipped_armor.def_bonus if self.equipped_armor else 0
        return self.base_defense + bonus
 
    def is_alive(self):
        return self.hp > 0
 
    def heal(self, hp_amount=0, mp_amount=0):
        before_hp = self.hp
        before_mp = self.mp
        self.hp = clamp(self.hp + hp_amount, 0, self.max_hp)
        self.mp = clamp(self.mp + mp_amount, 0, self.max_mp)
        return {
            'hp_recovered': self.hp - before_hp,
            'mp_recovered': self.mp - before_mp
        }
 
    def spend_mp(self, amount):
        if self.mp < amount:
            return False
        self.mp -= amount
        return True
 
    def add_exp(self, amount):
        self.exp += amount
        level_up_count = 0
        while self.exp >= self.next_level_exp:
            required = self.next_level_exp
            self.exp -= required
            self.level += 1
            level_up_count += 1
            self.max_hp += 15
            self.max_mp += 8
            self.base_attack += 3
            self.base_defense += 2
            self.hp = self.max_hp
            self.mp = self.max_mp
        return level_up_count
 
    def equip(self, item):
        if item.item_type == ItemType.WEAPON:
            self.equipped_weapon = item
            return True
        if item.item_type == ItemType.ARMOR:
            self.equipped_armor = item
            return True
        return False
 
    def status_text(self):
        weapon = self.equipped_weapon.name if self.equipped_weapon else '없음'
        armor = self.equipped_armor.name if self.equipped_armor else '없음'
        return (
            f'{self.name} | Lv.{self.level} | HP {self.hp}/{self.max_hp} | '
            f'MP {self.mp}/{self.max_mp} | ATK {self.total_attack} | '
            f'DEF {self.total_defense} | GOLD {self.gold} | '
            f'무기:{weapon} | 방어구:{armor}'
        )
 
print('✅ [모듈 5] Player 정의 완료')

# ===== 모듈 06 · 명령어 분석 =====
@dataclass
class Command:
    action: str
    target: Optional[str] = None
    extra: Optional[str] = None
 
class CommandParser:
    @staticmethod
    def parse(text):
        parts = text.strip().split()
        if len(parts) == 0:
            return Command('')
        action = parts[0]
        target = parts[1] if len(parts) >= 2 else None
        extra = ' '.join(parts[2:]) if len(parts) >= 3 else None
        return Command(action, target, extra)
 
print('✅ [모듈 6] CommandParser 정의 완료')

# ===== 모듈 07 · 피해 계산 =====
class DamageCalculator:
    @staticmethod
    def calculate(attack, defense, power=0, critical_chance=0.1):
        base = max(1, attack + power - defense)
        variance = random.randint(-2, 3)
        damage = max(1, base + variance)
        critical = random.random() < critical_chance
        if critical:
            damage = int(damage * 1.5)
        return {
            'damage': damage,
            'critical': critical,
            'attack': attack,
            'defense': defense,
            'power': power
        }
 
print('✅ [모듈 7] DamageCalculator 정의 완료')

# ===== 모듈 08 · 보상 처리 =====
class RewardManager:
    @staticmethod
    def give_reward(player, monster, item_catalog):
        player.gold += monster.gold_reward
        level_ups = player.add_exp(monster.exp_reward)
        dropped_item = None
        if monster.drop_item_id:
            chance = random.random()
            if chance < 0.65:
                dropped_item = item_catalog.get(monster.drop_item_id)
                if dropped_item:
                    player.inventory.add(dropped_item)
        return {
            'gold': monster.gold_reward,
            'exp': monster.exp_reward,
            'level_ups': level_ups,
            'dropped_item': dropped_item
        }
 
print('✅ [모듈 8] RewardManager 정의 완료')

# ===== 모듈 09 · 방·세계·이벤트 =====
@dataclass
class Room:
    id: str
    name: str
    description: str
    exits: Dict[Direction, str]
    monster_ids: List[str]
    item_ids: List[str]
    event_ids: List[str]
    npc_id: Optional[str] = None
    visited: bool = False
 
class World:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.current_room_id = 'town'
 
    def add_room(self, room):
        self.rooms[room.id] = room
 
    @property
    def current_room(self):
        return self.rooms[self.current_room_id]
 
    def move(self, direction):
        current = self.current_room
        if direction not in current.exits:
            return False
        self.current_room_id = current.exits[direction]
        self.current_room.visited = True
        return True
 
@dataclass
class GameEvent:
    id: str
    name: str
    condition: Callable[[Any], bool]
    action: Callable[[Any], None]
    once: bool = True
    triggered: bool = False
 
    def run(self, game):
        if self.once and self.triggered:
            return False
        if self.condition(game):
            self.action(game)
            self.triggered = True
            return True
        return False
 
class EventManager:
    def __init__(self):
        self.events: Dict[str, GameEvent] = {}
 
    def register(self, event):
        self.events[event.id] = event
 
    def trigger_room_events(self, game, room):
        for event_id in room.event_ids:
            event = self.events.get(event_id)
            if event:
                event.run(game)
 
print('✅ [모듈 9] World / Event 정의 완료')

# ===== 모듈 10 · NPC와 퀘스트 =====
@dataclass
class NPC:
    id: str
    name: str
    dialogue: List[str]
    quest_id: Optional[str] = None
 
class QuestManager:
    def __init__(self, quest_catalog):
        self.quest_catalog: Dict[str, Quest] = quest_catalog
 
    def talk_to_npc(self, game, npc):
        print(f'🧑 {npc.name}:')
        for sentence in npc.dialogue:
            print(' ', sentence)
        if not npc.quest_id:
            return
        quest = self.quest_catalog[npc.quest_id]
        if quest.status == QuestStatus.AVAILABLE:
            print(f"📜 퀘스트 '{quest.name}'를 수락했습니다.")
            quest.status = QuestStatus.ACTIVE
            if quest.id not in game.player.quest_ids:
                game.player.quest_ids.append(quest.id)
        elif quest.status == QuestStatus.ACTIVE:
            print(f'📜 진행도: {quest.progress}/{quest.required_count}')
        elif quest.status == QuestStatus.COMPLETED:
            print(f'🎉 퀘스트 완료! {quest.reward_gold}G를 받았습니다.')
            game.player.gold += quest.reward_gold
            if quest.reward_item_id:
                item = game.item_catalog.get(quest.reward_item_id)
                if item:
                    game.player.inventory.add(item)
                    print(f'🎁 보상 아이템: {item.name}')
            quest.status = QuestStatus.LOCKED
 
    def on_monster_defeated(self, game, monster):
        updated = []
        for quest_id in game.player.quest_ids:
            quest = self.quest_catalog.get(quest_id)
            if quest and quest.add_progress(monster.id):
                updated.append(quest)
        return updated
 
    def show_quests(self, player):
        if not player.quest_ids:
            print('📜 진행 중인 퀘스트가 없습니다.')
            return
        for quest_id in player.quest_ids:
            quest = self.quest_catalog[quest_id]
            print(f'📜 {quest.name} | {quest.status.name} |  
 
print('✅ [모듈 10] NPC / QuestManager 정의 완료')

# ===== 모듈 11 · 전투 =====
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

# ===== 모듈 12 · 저장·불러오기 =====
class SaveManager:
    SAVE_FILE = 'text_rpg_save.json'
 
    @staticmethod
    def save(game, file_name=None):
        file_name = file_name or SaveManager.SAVE_FILE
        data = {
            'saved_at': datetime.now().isoformat(),
            'player': {
                'name': game.player.name,
                'level': game.player.level,
                'exp': game.player.exp,
                'hp': game.player.hp,
                'max_hp': game.player.max_hp,
                'mp': game.player.mp,
                'max_mp': game.player.max_mp,
                'base_attack': game.player.base_attack,
                'base_defense': game.player.base_defense,
                'gold': game.player.gold,
                'inventory_ids': [item.id for item in game.player.inventory.items],
                'weapon_id': game.player.equipped_weapon.id if 
                'armor_id': game.player.equipped_armor.id if 
                'quest_ids': list(game.player.quest_ids),
            },
            'world': {
                'current_room_id': game.world.current_room_id,
                'visited_rooms': [room.id for room in game.world.rooms.values() 
            },
            'flags': list(game.flags),
            'quests': {
                quest_id: {'status': quest.status.name, 'progress': 
                for quest_id, quest in game.quest_catalog.items()
            }
        }
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return file_name
 
    @staticmethod
    def load(game, file_name=None):
        file_name = file_name or SaveManager.SAVE_FILE
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            return False
 
        p = data['player']
        player = game.player
        player.name = p['name']
        player.level = p['level']
        player.exp = p['exp']
        player.hp = p['hp']
        player.max_hp = p['max_hp']
        player.mp = p['mp']
        player.max_mp = p['max_mp']
        player.base_attack = p['base_attack']
        player.base_defense = p['base_defense']
        player.gold = p['gold']
        player.inventory.items.clear()
        for item_id in p['inventory_ids']:
            item = game.item_catalog.get(item_id)
            if item:
                player.inventory.add(item)
        player.equipped_weapon = 
        player.equipped_armor = 
        player.quest_ids = list(p.get('quest_ids', []))
 
        game.world.current_room_id = data['world']['current_room_id']
        visited_set = set(data['world']['visited_rooms'])
        for room in game.world.rooms.values():
            room.visited = room.id in visited_set
        game.flags = set(data.get('flags', []))
        for quest_id, quest_data in data.get('quests', {}).items():
            quest = game.quest_catalog.get(quest_id)
            if quest:
                quest.status = QuestStatus[quest_data['status']]
                quest.progress = quest_data['progress']
        return True
 
print('✅ [모듈 12] SaveManager 정의 완료')

# ===== 모듈 13 · 게임 데이터 만들기 =====
def build_item_catalog():
    items = [
        Item('wood_sword', '나무 검', ItemType.WEAPON,  
        Item('iron_sword', '철 검', ItemType.WEAPON, '공격력이 
        Item('leather_armor', '가죽 갑옷', ItemType.ARMOR, 
        Item('knight_armor', '기사 갑옷', ItemType.ARMOR, 
        Item('small_potion', '작은 포션', ItemType.POTION, 'HP 
        Item('mana_potion', '마나 포션', ItemType.POTION, 'MP 
        Item('ancient_key', '고대의 열쇠', ItemType.KEY, '봉인된 
        Item('wolf_fang', '늑대의 송곳니', ItemType.MATERIAL, 
    ]
    return {item.id: item for item in items}
 
def build_monster_catalog():
    monsters = [
        Monster('slime', '초록 슬라임', 40, 40, 10, 2, 35, 15, 
        Monster('wolf', '회색 늑대', 70, 70, 18, 5, 55, 25, 
        Monster('golem', '고대 골렘', 130, 130, 28, 12, 120, 70, 
        Monster('dragon', '검은 용', 260, 260, 42, 18, 300, 250, None),
    ]
    return {monster.id: monster for monster in monsters}
 
def build_quest_catalog():
    quests = [
        Quest('wolf_hunt', '늑대의 위협', '숲의 회색 늑대를 
    ]
    return {quest.id: quest for quest in quests}
 
def build_npc_catalog():
    npcs = [
        NPC('elder', '마을 장로', ['숲의 늑대 때문에 사람들이 다치고 
        NPC('merchant', '떠돌이 상인', ['좋은 물건이 필요하면 골드를 
    ]
    return {npc.id: npc for npc in npcs}
 
def build_world():
    world = World()
    world.add_room(Room('town', '시작 마을', '작은 광장과 
    world.add_room(Room('forest', '어두운 숲', '나무 사이에서 
    world.add_room(Room('shop', '상점 거리', '각종 장비와 
    world.add_room(Room('ruins', '고대 유적', '무너진 돌벽 
    world.add_room(Room('sealed_gate', '봉인된 문', '검은 
    world.add_room(Room('dragon_castle', '검은 용의 성', 
    world.current_room.visited = True
    return world
 
print('✅ [모듈 13] 게임 데이터 생성 함수 정의 완료')

# ===== 모듈 14 · 게임 흐름 연결 =====
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

# ===== 모듈 15 · 실행 =====
player_name = input('플레이어 이름을 입력하세요> ').strip()
if player_name == '':
    player_name = '용사'
game = Game(player_name)
game.run()

