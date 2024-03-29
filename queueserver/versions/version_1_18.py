from quarry.types.nbt import TagInt

from queueserver.versions import Version_1_17_1
from queueserver.protocol import Protocol


class Version_1_18(Version_1_17_1):
    protocol_version = 757
    chunk_format = '1.18'

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_18, self).__init__(protocol, bedrock)

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        settings['min_y'] = TagInt(-64)
        settings['height'] = TagInt(384)

        return settings

    def send_join_game(self):
        self.init_dimension_codec()

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?BB", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(self.dimension_codec),
                                  self.protocol.buff_type.pack_nbt(self.dimension_settings[self.current_chunk.dimension]),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(32),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("????", False, True, False, False))

