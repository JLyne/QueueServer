import json

from quarry.types.nbt import TagRoot, TagCompound
from quarry.types.uuid import UUID

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
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 1, 0, 1),
                                  self.protocol.buff_type.pack_string("default"))
        self.protocol.send_packet("respawn", self.protocol.buff_type.pack("iBq", 0, 0, 1),
                                  self.protocol.buff_type.pack_string("default"))

    def send_reset_world(self):
        data = [
            self.protocol.buff_type.pack_varint(0),
            self.protocol.buff_type.pack_nbt(TagRoot({'': TagCompound({})})),
            self.protocol.buff_type.pack_varint(1024),
        ]

        for i in range(0, 1024):
            data.append(self.protocol.buff_type.pack_varint(127))

        data.append(self.protocol.buff_type.pack_varint(0))
        data.append(self.protocol.buff_type.pack_varint(0))

        for x in range(-8, 8):
            for y in range(-8, 8):
                self.protocol.send_packet("chunk_data", self.protocol.buff_type.pack("ii?", x, y, True), *data)

    def send_keep_alive(self):
        self.protocol.send_packet("keep_alive", self.protocol.buff_type.pack("Q", 0))

    def spawn_viewpoint_entity(self, viewpoint):
        self.protocol.send_packet(
                'spawn_mob',
                self.protocol.buff_type.pack_varint(self.viewpoint_id),
                self.protocol.buff_type.pack_uuid(UUID.random()),
                self.protocol.buff_type.pack_varint(self.get_viewpoint_entity_type()),
                self.protocol.buff_type.pack("dddbbbhhh",
                                             viewpoint.get('x'),
                                             viewpoint.get('y'),
                                             viewpoint.get('z'),
                                             viewpoint.get('yaw_256'),
                                             viewpoint.get('pitch'),
                                             viewpoint.get('yaw_256'), 0, 0, 0))

    def get_viewpoint_entity_type(self):
        return 62

    def send_time(self):
        # Time of day
        self.protocol.send_packet('time_update',
                                  self.protocol.buff_type.pack("Qq", 0,
                                                               self.current_chunk.time
                                                               if self.current_chunk.cycle is True
                                                               else (0 - self.current_chunk.time)))

    def send_weather(self, rain=False):
        if self.current_chunk.weather == 'rain':
            if self.raining is False:
                self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 2, 0))
                self.raining = True
        elif self.raining is True:
            self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 1, 0))
            self.raining = False

    def send_chat_message(self, message):
        self.protocol.send_packet('chat_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("b", 1))

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                                  self.protocol.buff_type.pack_string(json.dumps({
                                      "text": "\n\ue300\n"
                                  })),
                                  self.protocol.buff_type.pack_string(json.dumps({"translate": ""})))

        self.protocol.send_packet("player_list_item",
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                                  self.protocol.buff_type.pack_string(self.protocol.display_name),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_varint(1),
                                  self.protocol.buff_type.pack_varint(0))

    def send_inventory(self):
        data = [
            self.protocol.buff_type.pack('Bh', 0, 46)
        ]

        for i in range(0, 46):
            data.append(self.protocol.buff_type.pack('?', False))

        self.protocol.send_packet('window_items', *data)
