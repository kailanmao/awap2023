from src.game_constants import RobotType, Direction, Team, TileState
from src.game_state import GameState, GameInfo
from src.player import Player
from src.map import TileInfo, RobotInfo
import random
from collections import deque
from random import choices
import numpy as np

class BotPlayer(Player):
    """
    Players will write a child class that implements (notably the play_turn method)
    """

    def __init__(self, team: Team):
        self.team = team
        return

    def is_valid_move(self, move_dir, rname, rob, game_state):
        if not game_state.can_move_robot(rname, move_dir):
            return False
        (newRow, newCol) = (rob.row + move_dir.value[0], rob.col + move_dir.value[1])
        dest_tile = game_state.get_map()[newRow][newCol]
        return (dest_tile.robot is None or dest_tile.robot.team != self.team)


    def play_turn(self, game_state: GameState) -> None:

        # get info
        ginfo = game_state.get_info()

        # get turn/team info
        width, height = len(ginfo.map), len(ginfo.map[0])

        # print info about the game
        # print(f"Turn {ginfo.turn}, team {ginfo.team}")
        # print("Map height", height)
        # print("Map width", width)

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


        # print("Ally tiles", ally_tiles) 
        # TileInfo(state=<TileState.TERRAFORMABLE: 1>, row=2, col=5, terraform=2, mining=0, robot=None)

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

        # Prob of spawning # log_prob: chance of spawning explorer decreases at late game
        # choices(population, weights)
        # e_prob = log_prob(GameState)
        # t_prob = 1 - e_prob
        def log_prob(t):
            # ginfo = game_state.get_info()
            # t = ginfo.turn
            if t > 1:
                prob = (1 - 1/np.sqrt(201 - t)) # 1/log(turn) => goes smaller and smaller
            else:
                prob = 1
            return prob

        # spawn on a random tile
        # print(f"My metal {game_state.get_metal()}")
        if len(ally_tiles) > 0:
            # pick a random one to spawn on
            if mnum > num_mines:
                spawn_type = random.choice([RobotType.EXPLORER, RobotType.TERRAFORMER])
            else:
                spawn_type = random.choice([RobotType.MINER, RobotType.EXPLORER, RobotType.TERRAFORMER])
                e_prob = 1 - ginfo.turn/200
                m_prob = (1 - e_prob)/2
                t_prob = 1 - e_prob - m_prob
                gg = [e_prob, m_prob, t_prob]
                #spawn_type = choices([RobotType.EXPLORER, RobotType.MINER, RobotType.TERRAFORMER], gg)
                #print(spawn_type)

            spawn_loc = random.choice(ally_tiles)
            if (spawn_type == RobotType.TERRAFORMER):
                for loc in ally_tiles:
                    if (-trange <= loc.terraform and loc.terraform <= trange):
                        spawn_loc = loc
                        break
            # spawn the robot
            # print(f"Spawning robot at {spawn_loc.row, spawn_loc.col}")
            # check if we can spawn here (checks if we can afford, tile is empty, and tile is ours)
            if game_state.can_spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col):
                game_state.spawn_robot(spawn_type, spawn_loc.row, spawn_loc.col)

        # iterate through dictionary of robots
        for rname, rob in robots.items():
            #print(f"Robot {rname} at {rob.row, rob.col}")

            # randomly move if possible
            all_dirs = [dir for dir in Direction]
            move_dir = random.choice(all_dirs)

            # check if we can move in this direction
            if self.is_valid_move(move_dir, rname, rob, game_state):
                if rob.type == RobotType.MINER:
                    if ((ginfo.map[rob.row][rob.col]).mining == 0):
                        mining_dir = game_state.optimal_path(rob.row, rob.col, max_mine_row, max_mine_col)[0]
                        if (self.is_valid_move(mining_dir, rname, rob, game_state)):
                            game_state.move_robot(rname, mining_dir)
                        else:
                            game_state.move_robot(rname, move_dir)
                elif rob.type == RobotType.EXPLORER:
                    if self.is_valid_move(move_dir, rname, rob, game_state):
                        game_state.move_robot(rname, move_dir)
                else: #rob.type == RobotType.TERRAFORMER
                    game_state.move_robot(rname, move_dir)
            # action if possible
            if game_state.can_robot_action(rname):
                game_state.robot_action(rname)

        

