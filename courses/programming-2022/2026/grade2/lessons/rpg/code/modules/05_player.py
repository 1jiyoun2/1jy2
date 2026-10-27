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
