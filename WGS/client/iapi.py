import time
import enum
import json
import flask
import requests
import dispatcher

server_ws_addr = None
server_ack = False
userid = hash(time.time())

class ServerClients(object):
    
    instance : object = None

    def __init__(self) -> None:
        self.clients = []

        self.__class__.instance = self

    def update_players(self, player_dict: dict):
        frame_ids = [c.userid for c in self.clients]
        
        for player in json.loads(player_dict)['players']:
            if(player['userid'] not in frame_ids):
                self.clients.append(Client(**player))

                continue

            for client in self.clients:
                if(client.userid == player['userid']):
                    client.update_cinfo(**player)
            
ServerClients()

class Client(object):

    def __init__(self, **info: dict) -> None:
        global userid
        self.userid = userid

        self.friend_datastructure        = info.get('friend_ds')       # a array of friends by userids and the status of userid
        self.detail_datastructure        = info.get('detail_ds')       # involves currency, items, etc ...
        self.configuration_datastructure = info.get('configuration_ds')# a mapping of the clients network configurations

    def update_cinfo(self, **info: dict) -> None:
        self.friend_datastructure        = info.get('friend_ds')       # a array of friends by userids and the status of userid
        self.detail_datastructure        = info.get('detail_ds')       # involves username, currency, items, etc ...
        self.configuration_datastructure = info.get('configuration_ds')# a mapping of the clients network configurations

    def dict_info(self):
        return {'userid': self.userid, 'friends': self.friend_datastructure, 'details': self.detail_datastructure, 'configuration': self.configuration_datastructure}


class WrappedFunctions:

    def send_message(client: Client, dest_client: Client, message: str):
        dispatcher.Dispatcher.instance.new_event(client, ActionFlags.CLIENT_SEND_MESSAGE.value, {'a': [client.dict_info(), message], 'b': dest_client.dict_info()})

    def register_connection(client: Client):
        dispatcher.Dispatcher.instance.new_event(client, ActionFlags.NEW_CLIENT.value, client.dict_info())

class ActionFlags(enum.Enum):

    NEW_CLIENT                  = 0xAF00# {'flag': -0xAF10, 'content': CLIENT_INFO_DICT} 
    CLIENT_ACK                  = 0xAF01# {'flag': 0xAF01} # response sent to client upon NEW_CLIENT completion

    UPDATE_CLIENT_INFO          = 0xAF10 # {'flag': 0xAF10, 'content': CLIENT_INFO_DICT} || ROUTE : route_update_client
    
    CLIENT_TRADE_REQUEST        = 0xAF20 # {'flag': 0xAF20, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}
    CLIENT_TRADE_REQUEST_ACCEPT = 0xAF21 # {'flag': 0xAF21, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}
    CLIENT_TRADE_REQUEST_DENY   = 0xAF22 # {'flag': 0xAF22, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}
    
    CLIENT_FRIEND_REQUEST       = 0xAF30 # {'flag': 0xAF30, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : SENDER | B : RECEIVER
    CLIENT_FRIEND_REQUEST_ACCEPT= 0xAF31 # {'flag': 0xAF31, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : REQUESTER | B : ACCEPTER
    CLIENT_FRIEND_REQUEST_DENY  = 0xAF32 # {'flag': 0xAF32, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : REQUESTER | B : ACCEPTER
    CLIENT_FRIEND_REMOVE        = 0xAF40 # {'flag': 0xAF40, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : SENDER | B : RECEIVER
    
    CLIENT_ADD_IGNORE           = 0xAF50 # {'flag': 0xAF50, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : SENDER | B : RECEIVER  || THIS IS HANDLED CLIENT SIDE
    CLIENT_REMOVE_IGNORE        = 0xAF60 # {'flag': 0xAF60, 'content': {'a': CLIENT_A_INFO_DICT, 'b' CLIENT_B_INFO_DICT}}             | A : SENDER | B : RECEIVER || THIS IS HANDLED CLIENT SIDE

    CLIENT_SEND_MESSAGE         = 0xAF70 # {'flag': 0xAF70, 'content': {'a': (CLIENT_A_INFO_DICT, MESSAGE), 'b': CLIENT_B_INFO_DICT}}  | A : SENDER | B : RECEIVER
    CLIENT_RECV_MESSAGE         = 0xAF80 # {'flag': 0xAF70, 'content': {'a': (CLIENT_A_INFO_DICT, MESSAGE)}}                           | A : SENDER               || THIS IS HANDLED CLIENT SIDE, JUST NEED TO SEND EVENT DETAILS

    CLIENT_RECEIVE_PLAYER_DISPATCH = 0xDF01 # {'flag': 0xDF01, 'content': {'players': [ClientList ( Replica of Client ) ]}}

def route_acknowledge_register(rq: flask.request, flag: int, content: dict): # called by the event handler
    global server_ack
    server_ack = True

def route_receive_player_dispatch(rq: flask.request, flag: int, content: dict):
    if(not content): # no players to dispatch
        return

    ServerClients.instance.update_players(content)


reverse_aflag_map = {
    ActionFlags.CLIENT_ACK.value: route_acknowledge_register,
    ActionFlags.CLIENT_RECEIVE_PLAYER_DISPATCH.value: route_receive_player_dispatch,
    ActionFlags.UPDATE_CLIENT_INFO.value: None,
    ActionFlags.CLIENT_TRADE_REQUEST.value: None,
    ActionFlags.CLIENT_TRADE_REQUEST_ACCEPT.value: None,
    ActionFlags.CLIENT_TRADE_REQUEST_DENY.value: None,
    ActionFlags.CLIENT_SEND_MESSAGE.value: None,
    ActionFlags.CLIENT_FRIEND_REQUEST: None,
    ActionFlags.CLIENT_FRIEND_REQUEST_ACCEPT.value: None,
    ActionFlags.CLIENT_FRIEND_REQUEST_DENY.value: None
}
