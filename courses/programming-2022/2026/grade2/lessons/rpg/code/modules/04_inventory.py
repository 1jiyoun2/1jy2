class Inventory:
    def __init__(self, capacity=12):
        self.items: List[Item] = []
        self.capacity = capacity
 
    def add(self, item):
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True
 
    def remove(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False
 
    def find_by_name(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None
 
    def find_by_id(self, item_id):
        for item in self.items:
            if item.id == item_id:
                return item
        return None
 
    def count_type(self, item_type):
        count = 0
        for item in self.items:
            if item.item_type == item_type:
                count += 1
        return count
 
    def list_items(self):
        if not self.items:
            print('🎒 인벤토리가 비어 있습니다.')
            return
        print(f'🎒 인벤토리 ({len(self.items)}/{self.capacity})')
        for index, item in enumerate(self.items, start=1):
            print(f'  {index}. {item.name} - {item.description}')
 
print('✅ [모듈 4] Inventory 정의 완료')
