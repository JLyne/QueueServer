from quarry.types.nbt import TagList, TagCompound, TagRoot, TagString, TagByte, TagFloat, TagLong, TagInt
from quarry.types.uuid import UUID

from versions import Version_1_15
from queueserver import Protocol

class Version_1_16(Version_1_15):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_16, self).__init__(protocol, bedrock)
        self.version_name = '1.16'

    def send_join_game(self):
        codec = TagRoot({
            '': TagCompound({
                'dimension': TagList([
                    TagCompound({
                        'name': TagString("minecraft:overworld"),
                        'natural': TagByte(1),
                        'ambient_light': TagFloat(0.0),
                        'has_ceiling': TagByte(0),
                        'has_skylight': TagByte(1),
                        'shrunk': TagByte(0),
                        'ultrawarm': TagByte(0),
                        'has_raids': TagByte(0),
                        'respawn_anchor_works': TagByte(0),
                        'bed_works': TagByte(0),
                        'piglin_safe': TagByte(0),
                        'logical_height': TagInt(255),
                        'infiniburn': TagString("minecraft:infiniburn_end"),
                    }),
                ])
            })
        })

        self.protocol.send_packet("join_game",
                         self.protocol.buff_type.pack("iBB", 0, 1, 1),
                         self.protocol.buff_type.pack_varint(2),
                         self.protocol.buff_type.pack_string("rtgame:queue"),
                         self.protocol.buff_type.pack_string("rtgame:reset"),
                         self.protocol.buff_type.pack_nbt(codec),
                         self.protocol.buff_type.pack_string("minecraft:overworld"),
                         self.protocol.buff_type.pack_string("rtgame:queue"),
                         self.protocol.buff_type.pack("qB", 0, 0),
                         self.protocol.buff_type.pack_varint(32),
                         self.protocol.buff_type.pack("????", False, True, False, False))

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string("minecraft:overworld"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_string("minecraft:overworld"),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))

    def spawn_viewpoint_entity(self, viewpoint):
        self.protocol.send_packet(
                'spawn_mob',
                self.protocol.buff_type.pack_varint(self.viewpoint_id),
                self.protocol.buff_type.pack_uuid(self.protocol.uuid),
                self.protocol.buff_type.pack_varint(68),
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
                                      self.protocol.buff_type.pack("b", 1),
                                      self.protocol.buff_type.pack_uuid(UUID(int=0)))
