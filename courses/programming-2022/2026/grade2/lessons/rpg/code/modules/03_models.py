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
