import random
player_hp = 100
player_mn = 100
player_def = 5
player_spd = 50
class Inventory:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def show(self):
        print("\nInventory:")
        if not self.items:
            print("  (empty)")
        else:
            for item in self.items:
                print(" ", item)

class Player:
    def __init__(self):
        self.inventory = Inventory()

player = Player()

name = input("Enter character name: ")
job = int(input("Choose your class (Enter corresponding number):\n1)Warrior\n2)Mage\n3)Rogue\n"))

if job == 1:
    player.inventory.add("Iron_ring")
    player_Patk = 10
    player_Matk = 30
    player_Mhp = 120
    player_Mmn = 30
    player_Pdef = 15
    player_Mdef = 10
    player_spd = 20
    player_cr = 15
    player_cd = 50
elif job == 2:
    player.inventory.add("Crystal_ring")
elif job == 3:
    player.inventory.add("Gold_ring")
else:
    print("Invalid choice")

print(name)
player.inventory.show()



