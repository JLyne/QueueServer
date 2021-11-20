from copy import deepcopy
from quarry.net.server import ServerProtocol

from quarry.types.uuid import UUID

from queueserver.log import console_handler, file_handler
from queueserver.prometheus import set_players_online

voting_mode = False
voting_secret = None

versions = {}


class Protocol(ServerProtocol):
    def __init__(self, factory, remote_addr):
        self.uuid = UUID.random()

        self.forwarded_uuid = None
        self.forwarded_host = None
        self.is_bedrock = False
        self.version = None

        super(Protocol, self).__init__(factory, remote_addr)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def packet_handshake(self, buff):
        buff2 = deepcopy(buff)
        super().packet_handshake(buff)

        buff2.unpack_varint()
        p_connect_host = buff2.unpack_string()

        # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
        split_host = str.split(p_connect_host, "\00")

        if len(split_host) >= 3:
            # TODO: Should probably verify the encrypted data in some way.
            # Not important until something on this server uses uuids
            if split_host[1] == 'Geyser-Floodgate':
                self.is_bedrock = True

                host = split_host[4]
                online_uuid = split_host[5]
            elif split_host[1].startswith('^Floodgate^'):
                self.is_bedrock = True

                host = split_host[2]
                online_uuid = split_host[3]
            else:
                host = split_host[1]
                online_uuid = split_host[2]

            self.forwarded_host = host
            self.forwarded_uuid = UUID.from_hex(online_uuid)

        version = None

        # Select version handler
        for protocol_version, v in versions.items():
            if self.protocol_version >= protocol_version:
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


# Build dictionary of protocol version -> version class
# Local import to prevent circlular import issues
def build_versions():
    import queueserver.versions

    for version in vars(queueserver.versions).values():
        if hasattr(version, 'protocol_version') and version.protocol_version is not None:
            versions[version.protocol_version] = version
