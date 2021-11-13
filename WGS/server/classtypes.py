import sys
import typing

sys.stdout.write(f'[*] Loading Reference {__name__}\n')

ClientList = typing.NewType('ClientList', list)

class ClientInformation(object):

    instances : ClientList = []

    @staticmethod
    def get_cinfo(userid: int):
        for instance in ClientInformation.instances:
            if(instance.userid == userid):
                return instance

    def __init__(self, remote_addr: object, **info: dict) -> None:
        sys.stdout.write(f'[*] [OBJECT] {self.__class__.__name__} Initialized ({hex(id(self))})\n')
        self.userid = info.get('userid')
        self.address = remote_addr

        self.friend_datastructure        = info.get('friend_ds')       # a array of friends by userids and the status of userid
        self.detail_datastructure        = info.get('detail_ds')       # involves currency, items, etc ...
        self.configuration_datastructure = info.get('configuration_ds')# a mapping of the clients network configurations

        self.__class__.instances.append(self)

    def update_cinfo(self, **info: dict) -> None:
        self.friend_datastructure        = info.get('friend_ds')       # a array of friends by userids and the status of userid
        self.detail_datastructure        = info.get('detail_ds')       # involves username, currency, items, etc ...
        self.configuration_datastructure = info.get('configuration_ds')# a mapping of the clients network configurations

    def dict_info(self):
        return {'userid': self.userid, 'friends': self.friend_datastructure, 'details': self.detail_datastructure, 'configuration': self.configuration_datastructure}
