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
