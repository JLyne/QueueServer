"""
Empty server that send the _bare_ minimum data to keep a minecraft client connected
"""
import logging
from argparse import ArgumentParser
from copy import deepcopy

from twisted.internet import reactor
from quarry.net.server import ServerFactory, ServerProtocol

from quarry.types.uuid import UUID

import config
from prometheus import set_players_online, init_prometheus

voting_mode = False
voting_secret = None

class Protocol(ServerProtocol):
    def __init__(self, factory, remote_addr):
        from versions import Version_1_15, Version_1_16, Version_1_16_2
        self.uuid = UUID.from_offline_player('NotKatuen')

        self.forwarded_uuid = None
        self.forwarded_host = None
        self.is_bedrock = False
        self.version = None
        self.versions = {
            578 : Version_1_15,
            736 : Version_1_16,
            751 : Version_1_16_2
        }

        super(Protocol, self).__init__(factory, remote_addr)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        p_protocol_version = buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
        split_host = str.split(p_connect_host, "\00")

        if len(split_host) >= 3:
            #TODO: Should probably verify the encrypted data in some way. Not important until something on this server uses uuids
            if split_host[1] == 'Geyser-Floodgate':
                self.is_bedrock = True

                host = split_host[4]
                online_uuid = split_host[5]
            else :
                host = split_host[1]
                online_uuid = split_host[2]

            self.forwarded_host = host
            self.forwarded_uuid = UUID.from_hex(online_uuid)

        version = None

        for pv, v in self.versions.items():
            if p_protocol_version >= pv:
                version = v

        if version is not None:
            self.version = version(self, self.is_bedrock)
        else:
            self.close("Unsupported Minecraft Version")

    def player_joined(self):
        # Overwrite with forwarded information if present
        if self.forwarded_uuid is not None:
            self.uuid = self.forwarded_uuid
            self.display_name_confirmed = True

        if self.forwarded_host is not None:
            self.connect_host = self.forwarded_host

        super().player_joined()

        set_players_online(len(self.factory.players))

        self.version.player_joined()
    def player_left(self):
        super().player_left()

        set_players_online(len(self.factory.players))

    def packet_chat_message(self, buff):
        self.version.packet_chat_message(buff)

    # Cycle through viewpoints when player clicks
    def packet_animation(self, buff):
        self.version.packet_animation(buff)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-a", "--host", default="127.0.0.1", help="bind address")
    parser.add_argument("-p", "--port", default=25567, type=int, help="bind port")
    parser.add_argument("-m", "--max", default=65535, type=int, help="player count")
    parser.add_argument("-r", "--metrics", default=None, type=int, help="expose prometheus metrics on specified port")
    parser.add_argument("-v", "--voting", action='store_true',
                        help="puts server in 'voting' mode - shows entry counts and prev/next buttons")
    parser.add_argument("-s", "--secret", type=str,
                        help="Shared secret for voting url HMAC")

    args = parser.parse_args()

    server_factory = ServerFactory()
    server_factory.protocol = Protocol
    server_factory.max_players = args.max
    server_factory.motd = "Queue Server"
    server_factory.online_mode = False
    server_factory.compression_threshold = 5646848

    metrics_port = args.metrics

    voting_mode = args.voting
    voting_secret = args.secret

    if voting_mode is True and voting_secret is None:
        logging.getLogger('main').error("You must provide a secret (-s) to use voting mode. Exiting.")
        exit(1)

    if metrics_port is not None:
        init_prometheus(metrics_port)

    config.load_chunk_config()

    server_factory.listen(args.host, args.port)
    print('Server started')
    print("Listening on {}:{}".format(args.host, args.port))
    reactor.run()