import os

from quarry.types.buffer import Buffer
from quarry.types.nbt import TagInt

from queueserver.versions import Version_1_16_2
from queueserver.protocol import Protocol
from queueserver.versions.version import parent_folder


class Version_1_17(Version_1_16_2):
    protocol_version = 755
    chunk_format = '1.17'

    empty_chunk_buffer = Buffer(open(os.path.join(parent_folder, 'empty_chunk', chunk_format + '.bin'), 'rb').read())
    empty_chunk_buffer.unpack("i")
    empty_chunk_buffer.unpack("i")

    empty_chunk = empty_chunk_buffer.read()

    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_17, self).__init__(protocol, bedrock)

    def get_dimension_settings(self):
        settings = super().get_dimension_settings()

        settings['min_y'] = TagInt(0)
        settings['height'] = TagInt(256)

        return settings

    def get_viewpoint_entity_type(self):
        return 74

    def send_spawn(self):
        self.protocol.send_packet("player_position_and_look",
                                  self.protocol.buff_type.pack("dddff?", 8, 70, -8, 0, 0, 0b00000),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?", False))

    def send_reset_world(self):
        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii", x, y), self.empty_chunk)
