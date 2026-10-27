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
