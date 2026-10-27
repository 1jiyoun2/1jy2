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
