import libtcodpy as libtcod
from message import message


class Fighter:
    # combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, xp=0, xp_gain=50, death_function=None):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.xp = xp
        self.xp_gain = xp_gain
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def take_damage(self, damage, attacker):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage
        # check for death. if there's a death function, call it
        if self.hp <= 0:
            attacker.grant_xp(self.xp_gain)
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        if target.fighter is None:
            return

        # a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage, self)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name +
                    ' but it has no effect!')

    def heal(self, amount):
        # heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def grant_xp(self, amount):
        level = self.level()
        self.xp += amount
        if self.level() > level:
            message('You leveled up!', libtcod.green)
            self.hp = self.max_hp

    def level(self):
        xp = 0
        delta = 100
        level = 0
        while xp <= self.xp:
            level += + 1
            xp += delta
            delta *= 1.1
        return level

    def next_xp(self, level):
        xp = 0
        delta = 100
        i = 0
        while i < level:
            i += + 1
            xp += delta
            delta *= 1.1
        return int(xp)


class BasicMonster:
    def __init__(self):
        self.owner = None

    # AI for a basic monster.
    def take_turn(self, map, player):
        # a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(map.fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y, map)

            # close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)


class ConfusedMonster:
    CONFUSE_RANGE = 5
    CONFUSE_NUM_TURNS = 10

    # AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.owner = None
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self, map, player):
        if self.num_turns > 0:  # still confused...
            # move in a random direction, and decrease the number of turns confused
            dx = libtcod.random_get_int(0, -1, 1)
            dy = libtcod.random_get_int(0, -1, 1)
            self.owner.move_by(dx, dy, map)
            self.num_turns -= 1
        # restore the previous AI (this one will be deleted because it's not referenced anymore)
        else:
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name +
                    ' is no longer confused!', libtcod.red)


class Item:
    def __init__(self, use_function=None):
        self.owner = None
        self.use_function = use_function

    # an item that can be picked up and used.
    def pick_up(self, map, player):
        # add to the player's inventory and remove from the map
        if len(player.inventory) >= 26:
            message('Your inventory is full, cannot pick up ' +
                    self.owner.name + '.', libtcod.red)
        else:
            player.inventory.append(self.owner)
            map.objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)

    def use(self, player):
        # just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                # destroy after use, unless it was cancelled for some reason
                player.inventory.remove(self.owner)

    def drop(self, player, map):
        # add to the map and remove from the player's inventory. also, place it at the player's coordinates
        map.objects.append(self.owner)
        player.inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

class Ladder:
    def __init__(self, use_function):
        self.owner = None
        self.use_function = use_function

    # an item that can be picked up and used.
    def ascend(self, objects):
        self.use_function()
