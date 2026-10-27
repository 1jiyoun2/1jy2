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
