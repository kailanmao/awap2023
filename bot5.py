from src.game_constants import RobotType, Direction, Team, TileState
from src.game_state import GameState, GameInfo
from src.player import Player
from src.map import TileInfo, RobotInfo
import random
from collections import deque

class BotPlayer(Player):
    """
    Players will write a child class that implements (notably the play_turn method)
    """
    
    def __init__(self, team: Team):
        self.team = team
        return

    def is_valid_move(self, move_dir, rname, rob, game_state):
        if game_state.can_move_robot(rname, move_dir):
            (newRow, newCol) = (rob.row + move_dir.value[0], rob.col + move_dir.value[1])
            dest_tile = game_state.get_map()[newRow][newCol]
            return (not (dest_tile is None) and (dest_tile.robot is None or dest_tile.robot.team != self.team))

    def is_valid_tile(self, game_state, row, col):
        ginfo = game_state.get_info()
        width, height = len(ginfo.map), len(ginfo.map[0])
        if (row < 0 or row >= height or col < 0 or col >= width):
            return False
        tile = ginfo.map[row][col]
        return not (tile is TileState.IMPASSABLE or tile is TileState.ILLEGAL)

    def play_turn(self, game_state: GameState) -> None:

        # get info
        ginfo = game_state.get_info()
        stringMap = game_state.get_str_map()

        # get turn/team info
        width, height = len(ginfo.map), len(ginfo.map[0])

        # print info about the game
        print(f"Turn {ginfo.turn}, team {ginfo.team}")
        print("Map height", height)
        print("Map width", width)

        # find un-occupied ally tile
        ally_tiles = []
        num_mines = 0
        (max_mine_val, max_mine_row, max_mine_col) = (0, 0, 0)
        for row in range(height):
            for col in range(width):
                # get the tile at (row, col)
                tile = ginfo.map[row][col]
                # skip fogged tiles
                if tile is not None: # ignore fogged tiles
                    if tile.robot is None: # ignore occupied tiles
                        if tile.terraform > 0: # ensure tile is ally-terraformed
                            ally_tiles += [tile]
                        if tile.mining > 0:
                            num_mines += 1
                        if tile.mining > max_mine_val:
                            max_mine_val = tile.mining
                            max_mine_row = row
                            max_mine_col = col


        print("Ally tiles", ally_tiles)

        # move robots
        robots = game_state.get_ally_robots()

        (enum, mnum, tnum) = (0, 0, 0)
        for rname, rob in robots.items():
            if rob.type == RobotType.EXPLORER:
                enum += 1
            elif rob.type == RobotType.MINER:
                mnum += 1
            else:
                tnum += 1

        trange = 3

        # spawn on a random tile
        print(f"My metal {game_state.get_metal()}")
        if len(ally_tiles) > 0:
            # pick a random one to spawn on
            if mnum > num_mines:
                spawn_type = random.choice([RobotType.EXPLORER, RobotType.TERRAFORMER])
            else:
                spawn_type = random.choice([RobotType.MINER, RobotType.EXPLORER, RobotType.TERRAFORMER])
            spawn_loc = random.choice(ally_tiles)
            if (spawn_type == RobotType.TERRAFORMER):
                for loc in ally_tiles:
                    if (-trange <= loc.terraform and loc.terraform <= trange):
                        spawn_loc = loc
                        break
            # spawn the robot
            print(f"Spawning robot at {spawn_loc.row, spawn_loc.col}")
            # check if we can spawn here (checks if we can afford, tile is empty, and tile is ours)
            if game_state.can_spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col):
                game_state.spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col)

        # iterate through dictionary of robots
        for rname, rob in robots.items():

            moved = False
            if rob.type == RobotType.MINER and stringMap[rob.row][rob.col]=="M":
                if rob.battery>=20:
                    pass
                else:
                    moved=True
                    (dir,num)=game_state.robot_to_base(rname,True)
                    if dir!=None:
                        game_state.move_robot(rname, dir)
    
            # randomly move if possible
            all_dirs = [dir for dir in Direction]
            move_dir = random.choice(all_dirs)

            # check if we can move in this direction
            if self.is_valid_move(move_dir, rname, rob, game_state) and moved==False:
                if (rob.battery < rob.action_cost):
                    return_dir = game_state.robot_to_base(rname, True)[0]
                    if (self.is_valid_move(return_dir, rname, rob, game_state)):
                        game_state.move_robot(rname, return_dir)
                    else:
                        game_state.move_robot(rname, move_dir)
                elif rob.type == RobotType.MINER:
                    if ((ginfo.map[rob.row][rob.col]).mining == 0):
                        mining_dir = game_state.optimal_path(rob.row, rob.col, max_mine_row, max_mine_col)[0]
                        if (self.is_valid_move(mining_dir, rname, rob, game_state)):
                            game_state.move_robot(rname, mining_dir)
                        else:
                            game_state.move_robot(rname, move_dir)
                elif rob.type == RobotType.EXPLORER:
                    (best_dir, best_fog) = (None, 0)
                    #greedily find best direction to move
                    for dir1 in Direction:
                        (row1, col1) = (rob.row + dir1.value[0], rob.col + dir1.value[1])
                        if (self.is_valid_tile(game_state, row1, col1)):
                            num_fog = 0
                            for dir2 in Direction:
                                (row2, col2) = (row1 + dir2.value[0], col1 + dir2.value[1])
                                if (row2 >= 0 and row2 < height and col2 >= 0 and col2 < width):
                                    tile = ginfo.map[row2][col2]
                                    if (tile is None):
                                        num_fog += 1
                            if (num_fog > best_fog):
                                (best_dir, best_fog) = (dir1, num_fog)
                    if (self.is_valid_move(best_dir, rname, rob, game_state)):
                        game_state.move_robot(rname, best_dir)
                    else:
                        game_state.move_robot(rname, move_dir)
                else: #rob.type == RobotType.TERRAFORMER
                    game_state.move_robot(rname, move_dir)
            # action if possible
            if game_state.can_robot_action(rname):
                game_state.robot_action(rname)
