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
