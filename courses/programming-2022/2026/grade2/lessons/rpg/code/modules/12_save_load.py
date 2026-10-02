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
