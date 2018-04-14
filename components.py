import libtcodpy as libtcod


class Fighter:
    # combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power


class BasicMonster:
    def __init__(self):
        self.owner = None

    # AI for a basic monster.
    def take_turn(self, map, player, objects):
        # a basic monster takes its turn. If you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(map.fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y, map, objects)

            # close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                print 'The attack of the ' + monster.name + \
                    ' bounces off your shiny metal armor!'
