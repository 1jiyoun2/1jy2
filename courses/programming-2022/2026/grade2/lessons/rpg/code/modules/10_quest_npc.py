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
