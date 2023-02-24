import json

from quarry.types.nbt import TagInt
from quarry.types.uuid import UUID

from queueserver.versions import Version_1_18_2


class Version_1_19(Version_1_18_2):
    protocol_version = 759

    chunk_format = '1.19'

    def send_join_game(self):
        self.init_dimension_codec()

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?Bb", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(self.dimension_codec),
                                  self.protocol.buff_type.pack_string(self.current_chunk.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(7),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack("?????", False, True, False, False, False))  # Extra False for not providing a death location

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_chunk.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string(self.current_chunk.dimension),  # Current dimension is now a string
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("????", False, False, True, False))

    def get_dimension_settings(self, name: str):
        settings = super().get_dimension_settings(name)

        # New dimension settings
        settings['monster_spawn_block_light_limit'] = TagInt(0)
        settings['monster_spawn_light_level'] = TagInt(0)

        return settings

    def get_viewpoint_entity_type(self):
        return 77

    def spawn_viewpoint_entity(self, viewpoint):
        self.protocol.send_packet(
                'spawn_object',  # All entity spawns now use spawn_object
                self.protocol.buff_type.pack_varint(self.viewpoint_id),
                self.protocol.buff_type.pack_uuid(UUID.random()),
                self.protocol.buff_type.pack_varint(self.get_viewpoint_entity_type()),
                self.protocol.buff_type.pack("dddbbbbhhh",
                                             viewpoint.get('x'),
                                             viewpoint.get('y'),
                                             viewpoint.get('z'),
                                             viewpoint.get('pitch'),
                                             viewpoint.get('yaw_256'),
                                             viewpoint.get('yaw_256'), 0, 0, 0, 0))

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
                                  self.protocol.buff_type.pack("??", False, False))  # Extra false for unsigned profile

    def send_chat_message(self, message):
        # Use system chat for all messages
        self.protocol.send_packet('system_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("b", 1))
