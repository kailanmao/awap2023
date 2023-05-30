from src.game_constants import RobotType, Direction, Team, TileState
from src.game_state import GameState, GameInfo
from src.player import Player
from src.map import TileInfo, RobotInfo
import random
import copy

class BotPlayer(Player):
    """
    Players will write a child class that implements 
    (notably the play_turn method)
    """

    def __init__(self, team: Team):
        self.team = team
        return

    def play_turn(self, game_state: GameState) -> None:

        # get info
        ginfo = game_state.get_info()

        # get turn/team info
        width, height = len(ginfo.map), len(ginfo.map[0])
        stringMap = game_state.get_str_map()

        # print info about the game
        print(f"Turn {ginfo.turn}, team {ginfo.team}")
        print("Map height", height)
        print("Map width", width)

        # find un-occupied ally tile
        ally_tiles = []
        for row in range(height):
            for col in range(width):
                # get the tile at (row, col)
                tile = ginfo.map[row][col]
                # skip fogged tiles
                if tile is not None: # ignore fogged tiles
                    if tile.robot is None: # ignore occupied tiles
                        if tile.terraform > 0: # ensure tile is ally-terraformed
                            ally_tiles += [tile]

        print("Ally tiles", ally_tiles)

        # spawn on a random tile
        if len(ally_tiles) > 0:
            # pick a random one to spawn on
            spawn_loc = random.choice(ally_tiles)
            spawn_type = random.choice([RobotType.MINER, RobotType.EXPLORER, RobotType.TERRAFORMER])
            # spawn the robot
            # check if we can spawn here (checks if we can afford, tile is empty, and tile is ours)
            if game_state.can_spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col):
                game_state.spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col)


        # move robots
        robots = game_state.get_ally_robots()

        # iterate through dictionary of robots
        for rname, rob in robots.items():
            moved = False
            if rob.type == RobotType.MINER and stringMap[rob.row][rob.col]=="M":
                if rob.battery>=20:
                    pass
                else:
                    (dir,num)=game_state.robot_to_base(rname,True)
                    game_state.move_robot(rname, dir)
                moved = True
            # elif (rob.type == RobotType.TERRAFORMER and stringMap[rob.row][rob.col]!="I"
            #       and stringMap[rob.row][rob.col]!="M" and stringMap[rob.row][rob.col]!="#"):
            #     tileNum = (int(stringMap[rob.row][rob.col]))
            #     if tileNum<=0 and rob.battery>=20:
            #         pass
            #     elif rob.battery<20:
            #         (dir,num)=game_state.robot_to_base(rname,True)
            #         game_state.move_robot(rname, dir)
            #     moved = True
            # randomly move if possible
            all_dirs = [dir for dir in Direction]
            move_dir = random.choice(all_dirs)
            # hasMoved = False

            # check if we can move in this direction
            if game_state.can_move_robot(rname, move_dir) and moved==False:
                # try to not collide into robots from our team
                dest_loc = (rob.row + move_dir.value[0], rob.col + move_dir.value[1])
                dest_tile = game_state.get_map()[dest_loc[0]][dest_loc[1]]

                if dest_tile.robot is None or dest_tile.robot.team != self.team:
                    game_state.move_robot(rname, move_dir)

            # if rob.type == RobotType.TERRAFORMER and int(stringMap[rob.row][rob.col])>5 and hasMoved==False:
            #     temp_dirs = copy.copy(all_dirs)
            #     while len(temp_dirs)>0:
            #         random_dir = random.choice(temp_dirs)
            #         if game_state.can_move_robot(rname, random_dir):
            #             # try to not collide into robots from our team
            #             dest_loc = (rob.row + random_dir.value[0], rob.col + random_dir.value[1])
            #             dest_tile = game_state.get_map()[dest_loc[0]][dest_loc[1]]

            #             if dest_tile.robot is None or dest_tile.robot.team != self.team:
            #                 game_state.move_robot(rname, random_dir)
            #             break
            #         temp_dirs.remove(random_dir)



            # action if possible
            if game_state.can_robot_action(rname):
                game_state.robot_action(rname)
