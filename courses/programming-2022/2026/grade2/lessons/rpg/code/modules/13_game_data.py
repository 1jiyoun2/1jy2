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
