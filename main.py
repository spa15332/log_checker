import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

import json
import os

# Class


class Activity():
    def __init__(self, activity):
        self.activity = activity
        self.dealer = activity["dealer"]
        self.player = activity["player"]
        self.event = activity["event"]
        self.contents = activity["contents"]
        self.turn = activity["turn"] if "turn" in activity else None

    def __str__(self):
        return json.dumps(self.activity, indent=2, ensure_ascii=False)

class Turn():
    def __init__(self, activity):
        self.turn = activity.turn
        self.first_player = activity.contents["first_player"]
        self.white_wild = activity.contents["white_wild"]
        self.first_card = activity.contents["first_card"]
        self.play_order = activity.contents["play_order"]
        self.cards_receive = activity.contents["cards_receive"]
        self.activities = []

        self.special_logic_exists = False
        self.color_change_request_exists = False
        self.color_of_wild_exists = False
        self.play_draw_card_exists = False
        self.challenge_exists = False
        self.shuffle_wild_exists = False
        self.public_card_exists = False
        self.penalty_exists = False

    def get_turn_data(self):
        turn_data = {}
        turn_data["special_logic_exists"] = self.special_logic_exists
        turn_data["color_change_request_exists"] = self.color_change_request_exists
        turn_data["color_of_wild_exists"] = self.color_of_wild_exists
        turn_data["play_draw_card_exists"] = self.play_draw_card_exists
        turn_data["challenge_exists"] = self.challenge_exists
        turn_data["shuffle_wild_exists"] = self.shuffle_wild_exists
        turn_data["public_card_exists"] = self.public_card_exists
        turn_data["penalty_exists"] = self.penalty_exists

        return turn_data

    def make_activities(self):
        activities = self.activities
        players = list(self.cards_receive.keys())

        res_list = []
        for activity in activities:
            temp_list = [""]*7
            temp_list[0] = [activity.event]

            if activity.event == "first-player":
                played_card = activity.contents["first_card"]
                temp_list[1] = [self.parse_card(played_card)]
                for i in range(4):
                    temp_list[i+2] = sorted([self.parse_card(a) for a in activity.contents["cards_receive"][players[i]]])
                first_player = activity.contents["first_player"]
                index = players.index(first_player)
                temp_list[index+2] += ["","First Player"]

            if activity.event == "next-player":
                played_card = activity.contents["card_before"]
                temp_list[1] = [self.parse_card(played_card)]
                next_player = activity.contents["next_player"]
                index = players.index(next_player)
                temp_list[index+2] = sorted([self.parse_card(a) for a in activity.contents["card_of_player"]])
                if not activity.contents["turn_right"]:
                    temp_list[6] = ["R"]

            if activity.event == "play-card":
                played_card = activity.contents["card_play"]
                temp_list[1] = [self.parse_card(played_card)]
                player = activity.player
                index = players.index(player)
                temp_list[index+2] = [self.parse_card(activity.contents["card_play"])]

            if activity.event == "special-logic":
                player = activity.player
                index = players.index(player)
                temp_list[index+2] = [activity.contents["title"]]

            if activity.event == "shuffle-wild":
                for i in range(4):
                    temp_list[i+2] = sorted([self.parse_card(a) for a in activity.contents["cards_receive"][players[i]]])

            if activity.event == "color-change-request":
                player = activity.contents["player"]
                index = players.index(player)
                temp_list[index+2] = ["↓"]

            if activity.event == "color-of-wild":
                player = activity.player
                index = players.index(player)
                if "color_of_wild" in activity.contents:
                    temp_list[index+2] = [self.parse_color_of_wild(activity.contents["color_of_wild"])]
                else:
                    temp_list[index+2] = ["×"]

            if activity.event == "draw-card":
                player = activity.player
                index = players.index(player)
                temp_list[index+2] = sorted([self.parse_card(a) for a in activity.contents["card_draw"]])

            if activity.event == "play-draw-card":
                player = activity.player
                index = players.index(player)
                if "card_play" in activity.contents:
                    temp_list[index+2] = [self.parse_card(activity.contents["card_play"])]
                else:
                    temp_list[index+2] = ["no card play"]

            if activity.event == "penalty":
                player = activity.contents["player"]
                index = players.index(player)
                temp_list[index+2] = sorted([self.parse_card(a) for a in activity.contents["cards_receive"]])
                
                temp_list[index+2] += ["", activity.contents["error"]]

            if activity.event == "public-card":
                player = activity.contents["player"]
                index = players.index(player)
                temp_list[index+2] = sorted([self.parse_card(a) for a in activity.contents["cards"]])


            if activity.event == "challenge":
                src_player = activity.player
                src_index = players.index(src_player)
                target_player = activity.contents["target"]
                target_index = players.index(target_player)
                if activity.contents["is_challenge"]:
                    if activity.contents["result"]["is_challenge_success"]:
                        temp_list[src_index+2] = ["※チャレンジ成功"]
                        temp_list[target_index+2] = sorted([self.parse_card(a) for a in activity.contents["result"]["cards_receive"]])
                    else:
                        temp_list[src_index+2] = sorted([self.parse_card(a) for a in activity.contents["result"]["cards_receive"]])
                        temp_list[target_index+2] = ["※チャレンジ失敗"]
                else:
                    temp_list[src_index+2] = ["チャレンジせず"]

            if activity.event == "say-uno-and-play-card":
                played_card = activity.contents["card_play"]
                temp_list[1] = [self.parse_card(played_card)]
                player = activity.player
                index = players.index(player)
                temp_list[index+2] = sorted([self.parse_card(activity.contents["card_play"])])

            if activity.event == "finish-turn":
                for i in range(4):
                    temp_list[i+2] = sorted([self.parse_card(a) for a in activity.contents["card_of_player"][players[i]]])
                    if players[i] not in activity.contents["score"]: activity.contents["score"][players[i]]=-99999999
                    temp_list[i+2] += ["", "score: " + str(activity.contents["score"][players[i]])]
                    temp_list[i+2] += ["", "total_score: " + str(activity.contents["total_score"][players[i]])]

            res_list.append(temp_list)

        return res_list, players

    def parse_card(self, arg):
        if type(arg)==dict:
            if "color" in arg and "number" in arg:
                return arg["color"] + ": " + str(arg["number"])
            elif "color" in arg and "special" in arg:
                return arg["color"] + ": " + arg["special"]
        return arg

    def parse_color_of_wild(self, arg):
        return arg

    def __str__(self):
        temp = {}
        temp["turn"] = self.turn
        temp["first_player"] = self.first_player
        temp["white_wild"] = self.white_wild
        temp["first_card"] = self.first_card
        temp["play_order"] = self.play_order
        return json.dumps(temp, indent=2, ensure_ascii=False)

class UnparsedTurn(Turn):
    def __init__(self, turn:Turn):
        self.activities = turn.activities
        self.cards_receive = turn.cards_receive

    def parse_card(self, arg):
        special_dict = {
            "wild": "W",
            "skip": "Sk",
            "reverse": "Rv",
            "white_wild": "WhW",
            "draw_2": "D2",
            "wild_draw_4": "WD4",
            "wild_shuffle": "WSh"
            }
        if type(arg)==dict:
            if "color" in arg and "number" in arg:
                return [arg["color"], str(arg["number"])]
            elif "color" in arg and "special" in arg:
                return [arg["color"], special_dict[arg["special"]]]
        return arg

    def parse_color_of_wild(self, arg):
        return [arg, arg]

class Game():
    def __init__(self, path):
        self.path = path
        self.players = {}
        self.turns = []
        self._load_log(path)

    def _load_log(self, path):
        with open(path) as f:
            lines = f.readlines()

        for i, l in enumerate(lines):
            if i < 1000000:
                activity = Activity(json.loads(l))

                if activity.event == "join-room":
                    self.players[activity.contents["player_id"]
                                 ] = activity.contents["player_name"]
                elif activity.event == "first-player":
                    turn = Turn(activity)
                    turn.activities.append(activity)
                elif activity.event == "finish-turn":
                    turn.activities.append(activity)
                    self.turns.append(turn)
                elif activity.event == "finish-game":
                    self.finish_game_activity = activity
                elif activity.event == "disconnect":
                    pass

                else:
                    if activity.event == "special-logic":
                        turn.special_logic_exists = True
                    elif activity.event == "color-change-request":
                        turn.color_change_request_exists = True
                    elif activity.event == "color-of-wild":
                        turn.color_of_wild_exists = True
                    elif activity.event == "play-draw-card":
                        turn.play_draw_card_exists = True
                    elif activity.event == "challenge":
                        turn.challenge_exists = True
                    elif activity.event == "shuffle-wild":
                        turn.shuffle_wild_exists = True
                    elif activity.event == "public-card":
                        turn.public_card_exists = True
                    elif activity.event == "penalty":
                        turn.penalty_exists = True

                    turn.activities.append(activity)

    def __str__(self):
        return json.dumps(self.finish_game_activity.activity, indent=2, ensure_ascii=False)


# const
BASE_DIR = os.getcwd() + "/"
LOGS_DIR = "logs/"


# FasrAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def root(request: Request):
    path = BASE_DIR + LOGS_DIR
    files = os.listdir(path)

    return templates.TemplateResponse("root.html", {"request": request, "files": files})


@app.get("/{dealer_name}")
def game(request: Request, dealer_name):

    path = BASE_DIR + LOGS_DIR + dealer_name + ".log"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="log_not_found")
    game = Game(path)

    turn_data = [t.get_turn_data() for t in game.turns]

    return templates.TemplateResponse("game.html", {"request": request, "dealer_name": dealer_name, "N": len(game.turns), "turn_data": turn_data})


@app.get("/{dealer_name}/{turn_num}")
def turn(request: Request, dealer_name, turn_num):
    path = BASE_DIR + LOGS_DIR + dealer_name + ".log"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="log_not_found")
    game = Game(path)

    res_list, players = game.turns[int(turn_num)].make_activities()
    players = [game.players[p] for p in players]

    return templates.TemplateResponse("turn.html", {"request": request, "dealer_name": dealer_name, "turn_num": turn_num, "players": players, "res_list": res_list})

@app.get("/{dealer_name}/{turn_num}/transformed")
def transformed_turn(request: Request, dealer_name, turn_num):
    path = BASE_DIR + LOGS_DIR + dealer_name + ".log"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="log_not_found")
    game = Game(path)

    unpersed_turn = UnparsedTurn(game.turns[int(turn_num)])
    res_list, players = unpersed_turn.make_activities()
    players = [game.players[p] for p in players]

    return templates.TemplateResponse("transformed_turn.html", {"request": request, "dealer_name": dealer_name, "turn_num": turn_num, "players": players, "res_list": res_list})


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8001)
