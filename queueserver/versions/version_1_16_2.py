import os

from quarry.types.nbt import TagList, TagCompound, TagRoot, TagString, TagByte, TagFloat, TagInt, NBTFile
from quarry.types.uuid import UUID

from queueserver.versions import Version_1_16
from queueserver.server import Protocol, path


class Version_1_16_2(Version_1_16):
    def __init__(self, protocol: Protocol, bedrock: False):
        super(Version_1_16_2, self).__init__(protocol, bedrock)
        self.version_name = '1.16.2'

        self.dimension_settings = self.get_dimension_settings()

        self.dimension = {
            'name': TagString("minecraft:overworld"),
            'id': TagInt(0),
            'element': TagCompound(self.dimension_settings),
        }

        self.current_dimension = TagRoot({
            '': TagCompound(self.dimension_settings),
        })

        self.biomes = NBTFile(TagRoot({})).load(os.path.join(path, 'biomes', '1.16.2.nbt'))

    def get_dimension_settings(self):
        return {
            'name': TagString("minecraft:overworld"),
            'natural': TagByte(1),
            'ambient_light': TagFloat(1.0),
            'has_ceiling': TagByte(0),
            'has_skylight': TagByte(1),
            'ultrawarm': TagByte(0),
            'has_raids': TagByte(0),
            'respawn_anchor_works': TagByte(0),
            'bed_works': TagByte(0),
            'piglin_safe': TagByte(0),
            'infiniburn': TagString("minecraft:infiniburn_overworld"),
            "effects": TagString("minecraft:overworld"),
            'logical_height': TagInt(256),
            'coordinate_scale': TagFloat(1.0),
        }

    def send_join_game(self):
        codec = TagRoot({
            '': TagCompound({
                'minecraft:dimension_type': TagCompound({
                    'type': TagString("minecraft:dimension_type"),
                    'value': TagList([
                        TagCompound(self.dimension)
                    ]),
                }),
                'minecraft:worldgen/biome': self.biomes.root_tag.body
            })
        })

        self.protocol.send_packet("join_game",
                                  self.protocol.buff_type.pack("i?BB", 0, False, 1, 1),
                                  self.protocol.buff_type.pack_varint(2),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack_nbt(codec),
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("q", 0),
                                  self.protocol.buff_type.pack_varint(0),
                                  self.protocol.buff_type.pack_varint(32),
                                  self.protocol.buff_type.pack("????", False, True, False, False))

    def send_respawn(self):
        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:reset"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))

        self.protocol.send_packet("respawn",
                                  self.protocol.buff_type.pack_nbt(self.current_dimension),
                                  self.protocol.buff_type.pack_string("rtgame:queue"),
                                  self.protocol.buff_type.pack("qBB", 0, 1, 1),
                                  self.protocol.buff_type.pack("???", False, False, True))

    def get_viewpoint_entity_type(self):
        return 69

    def send_chat_message(self, message):
        self.protocol.send_packet('chat_message',
                                  self.protocol.buff_type.pack_string(message),
                                  self.protocol.buff_type.pack("b", 1),
                                  self.protocol.buff_type.pack_uuid(UUID(int=0)))
