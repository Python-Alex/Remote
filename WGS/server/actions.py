
import enum
import json
import flask
import typing
import throttle
import dispatcher
import classtypes

PackedClientInfo = typing.NewType('packed_cinfo', (dict, str))

class UserAlreadyExists(Exception):

    def __init__(self, *args: object) -> Exception:
        Exception.__init__(self, args)

class NoUserIDFound(Exception):

    def __init__(self, *args: object) -> Exception:
        Exception.__init__(self, args)

class MissingPacketData(Exception):

    def __init__(self, *args: object) -> Exception:
        Exception.__init__(self, args)

class MissingMessageInput(Exception):

    def __init__(self, *args: object) -> Exception:
        Exception.__init__(self, args)

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

    CLIENT_AUTHORIZATION_SEND   = 0xAFA1 # {'flag}: 0xAFA1, 'content': {'username': STR, 'password': STR}}

@throttle.GlobalTimeQueue.throttle_function(2.5)
def periodical_client_dispatch():
    if(len(dispatcher.ServerClients.instance.clients) == 0):
        return

    playerlist_frame = json.dumps({'players': [client.dict_info() for client in dispatcher.ServerClients.instance.clients]})

    for client in classtypes.ClientInformation.instances:
        dispatcher.Dispatcher.instance.new_event(client.userid, ActionFlags.CLIENT_RECEIVE_PLAYER_DISPATCH.value, playerlist_frame)

periodical_client_dispatch()

def route_new_client(rq: flask.request, flag: int, content: dict):
    pdata = content if(isinstance(content, dict)) else json.loads(content)

    if(not pdata):
        raise MissingPacketData('no content in packet')

    for client in classtypes.ClientInformation.instances:
        if(client.userid == pdata['userid']):
            raise UserAlreadyExists('the user already exists with this userid')

    c = classtypes.ClientInformation(rq.remote_addr, **pdata)

    dispatcher.ServerClients.instance.clients.append(c)

    dispatcher.Dispatcher.instance.new_event(pdata['userid'], ActionFlags.CLIENT_ACK.value,'successfully joined server')
    

def route_update_client(rq: flask.request, flag: int, content: dict):
    pdata = json.loads(content)
    """when CLIENT A tells SERVER it's UPDATING

    Args:
        pdata (dict): [packet data dictionary]

    """
    a_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    return a_cinfo.update_cinfo(**pdata)

def route_trade_request(rq: flask.request, flag: int, content: dict):
    """when CLIENT A requests CLIENT B to prompt TRADE REQUEST

    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(pdata['b']['userid'], ActionFlags.CLIENT_TRADE_REQUEST.value, {'a': pdata['a'], 'b': pdata['b']})

def route_trade_request_accept(rq: flask.request, flag: int, content: dict):
    """when CLIENT B accepts TRADE REQUEST from CLIENT A, tell CLIENT A CLIENT B ACCEPTED
    
    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)
    
    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(pdata['a']['userid'], ActionFlags.CLIENT_TRADE_REQUEST_ACCEPT.value, {'a': pdata['a'], 'b': pdata['b']})

def route_trade_request_deny(rq: flask.request, flag: int, content: dict):
    """when CLIENT B accepts TRADE REQUEST from CLIENT A, tell CLIENT A CLIENT B ACCEPTED
    
    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise MissingPacketData('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(pdata['a']['userid'], ActionFlags.CLIENT_TRADE_REQUEST_DENY.value, {'a': pdata['a'], 'b': pdata['b']})

def route_send_message(rq: flask.request, flag: int, content: dict):
    """[summary]

    Args:
        pdata (dict): [description]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]

        NoUserIDFound: [a_cinfo: when client a is not found in client list]

        MissingMessageInput: [the given field was empty]
        
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)
    print('message', flag, content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : PackedClientInfo = classtypes.ClientInformation.get_cinfo(pdata['a'][0]['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))
    
    if(not pdata['a'][1]):
        raise MissingMessageInput('no message input')

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(b_cinfo.userid, ActionFlags.CLIENT_RECV_MESSAGE.value, {'a': (pdata['a'][0], pdata['a'][1]), 'b': pdata['b']})

def route_send_friend_request(rq: flask.request, flag: int, content: dict):
    """when CLIENT A sends CLIENT B a FRIEND REQUEST, awaiting DENY/ACCEPT

    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        MissingMessageInput: [the given field was empty]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : PackedClientInfo = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(b_cinfo.userid, ActionFlags.CLIENT_FRIEND_REQUEST.value, {'a': (pdata['a'], pdata['b'])})

def route_friend_request_accept(rq: flask.request, flag: int, content: dict):
    """when CLIENT B accepts CLIENT A's friend request

    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        MissingMessageInput: [the given field was empty]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : PackedClientInfo = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(a_cinfo.userid, ActionFlags.CLIENT_FRIEND_REQUEST_ACCEPT.value, {'a': (pdata['a'], pdata['b'])})

def route_friend_request_deny(rq: flask.request, flag: int, content: dict):
    """when CLIENT B denys CLIENT A's friend request

    Args:
        pdata (dict): [packet data dictionary]

    Raises:
        MissingPacketData: [pdata: when key a or b is not specified]
        NoUserIDFound: [a_cinfo: when client a is not found in client list]
        MissingMessageInput: [the given field was empty]
        NoUserIDFound: [b_cinfo: when client b is not found in client list]
    """
    pdata = json.loads(content)

    if(not pdata.get('a') or not pdata.get('b')):
        raise MissingPacketData('missing data from packet data')

    a_cinfo : PackedClientInfo = classtypes.ClientInformation.get_cinfo(pdata['a']['userid'])
    if(not a_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['a']['userid']))

    b_cinfo : classtypes.ClientInformation = classtypes.ClientInformation.get_cinfo(pdata['b']['userid'])
    if(not b_cinfo):
        raise NoUserIDFound('failed to find userid %d' % (pdata['b']['userid']))

    dispatcher.Dispatcher.instance.new_event(a_cinfo.userid, ActionFlags.CLIENT_FRIEND_REQUEST_DENY.value, {'a': (pdata['a'], pdata['b'])})


reverse_aflag_map = {
    ActionFlags.NEW_CLIENT.value: route_new_client,
    ActionFlags.UPDATE_CLIENT_INFO.value: route_update_client,
    ActionFlags.CLIENT_TRADE_REQUEST.value: route_trade_request,
    ActionFlags.CLIENT_TRADE_REQUEST_ACCEPT.value: route_trade_request_accept,
    ActionFlags.CLIENT_TRADE_REQUEST_DENY.value: route_trade_request_deny,
    ActionFlags.CLIENT_SEND_MESSAGE.value: route_send_message,
    ActionFlags.CLIENT_FRIEND_REQUEST: route_send_friend_request,
    ActionFlags.CLIENT_FRIEND_REQUEST_ACCEPT.value: route_friend_request_accept,
    ActionFlags.CLIENT_FRIEND_REQUEST_DENY.value: route_friend_request_deny
}
