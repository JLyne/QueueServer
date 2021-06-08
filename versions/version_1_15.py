from versions import Version

from queueserver import Protocol

class Version_1_15(Version):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_15, self).__init__(protocol, bedrock)
        self.version_name = '1.15'

    def send_join_game(self):
        self.protocol.send_packet("join_game",
                         self.protocol.buff_type.pack("iBqiB", 0, 1, 0, 0, 0),
                         self.protocol.buff_type.pack_string("default"),
                         self.protocol.buff_type.pack_varint(16),
                         self.protocol.buff_type.pack("??", False, True))

    def send_spawn(self):
        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?", 16, 64, -16, 0, 0, 0b00000),
                                  self.protocol.buff_type.pack_varint(0))

    def send_respawn(self):
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 1, 0, 1), self.protocol.buff_type.pack_string("default"))
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 0, 0, 1), self.protocol.buff_type.pack_string("default"))

    def spawn_viewpoint_entity(self, viewpoint):
        self.protocol.send_packet(
                'spawn_mob',
                self.protocol.buff_type.pack_varint(self.viewpoint_id),
                self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                self.protocol.buff_type.pack_varint(62),
                self.protocol.buff_type.pack("dddbbbhhh",
                                    viewpoint.get('x'),
                                    viewpoint.get('y'),
                                    viewpoint.get('z'),
                                    viewpoint.get('yaw_256'),
                                    viewpoint.get('pitch'),
                                    viewpoint.get('yaw_256'), 0, 0, 0))

    def send_chat_message(self, message):
        self.protocol.send_packet('chat_message',
                                      self.protocol.buff_type.pack_string(message),
                                      self.protocol.buff_type.pack("b", 1))

    def send_inventory(self):
        data = [
            self.protocol.buff_type.pack('Bh', 0, 46)
        ]

        for i in range(0, 46):
            data.append(self.protocol.buff_type.pack('?', False))

        self.protocol.send_packet('window_items', *data)