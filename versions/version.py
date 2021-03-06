import abc
import json
import random
import time

from quarry.types.nbt import TagRoot, TagCompound
from quarry.types.uuid import UUID

import config
from queueserver import Protocol, voting_mode, voting_secret
from voting import entry_json, entry_navigation_json


class Version(object, metaclass=abc.ABCMeta):
    def __init__(self, protocol: Protocol, bedrock: False):
        self.protocol = protocol
        self.viewpoint_id = 999

        self.current_chunk = None
        self.current_viewpoint = None
        self.raining = False

        self.player_spawned = False
        self.viewpoint_spawned = False
        self.viewpoint_used = False

        self.last_click = time.time()

        self.version_name = None
        self.is_bedrock = bedrock

    def player_joined(self):
        self.send_join_game()

        if voting_mode:
            self.current_chunk = config.chunks[self.version_name][0]
        else:
            self.current_chunk = random.choice(config.chunks[self.version_name])

        self.protocol.ticker.add_loop(100, self.send_keep_alive)  # Keep alive packets
        self.protocol.ticker.add_delay(10, self.send_tablist)

        self.send_inventory()
        self.send_chunk()

    # Handle /next and /orev commands in voting mode
    def packet_chat_message(self, buff):
        message = buff.unpack_string()

        if voting_mode is False:
            return

        if message == "/prev":
            self.previous_chunk()
        elif message == "/next":
            self.next_chunk()

    def packet_animation(self, buff):
        buff.unpack_varint()

        if self.is_bedrock:
            return

        now = time.time()

        # Prevent spam
        if now - self.last_click > 0.5:
            self.last_click = now
            self.next_viewpoint()

    def send_chunk(self):
        # Clear geyser chunk cache from previous server
        if self.is_bedrock:
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

        self.current_viewpoint = 0
        self.send_viewpoint()

        # Chunk packets
        for packet in  self.current_chunk.packets:
            self.protocol.send_packet(packet.get('type'), packet.get('packet'))


        # Start/stop rain as necessary
        if self.current_chunk.weather == 'rain':
            if self.raining is False:
                self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 2, 0))
                self.raining = True
        elif self.raining is True:
            self.protocol.send_packet('change_game_state', self.protocol.buff_type.pack("Bf", 1, 0))
            self.raining = False

        if self.is_bedrock: # Current versions of geyser seem to ignore the time sometimes. Send repeatedly for now.
            self.protocol.ticker.add_loop(100, self.send_time)
        else:
            self.send_time()

        if voting_mode:
            self.send_chat_message(entry_json(
                                          config.chunks[self.version_name].index(self.current_chunk) + 1, len(
                                          config.chunks[self.version_name])))
        # Credits
        self.send_chat_message(self.current_chunk.credit_json())

        if voting_mode and not self.is_bedrock:
            self.send_chat_message(entry_navigation_json(self.protocol.uuid, voting_secret))

    def send_viewpoint(self):
        viewpoint =  self.current_chunk.viewpoints[self.current_viewpoint]
        x = viewpoint.get('x')
        z = viewpoint.get('z')
        y = viewpoint.get('y')

        # Player hasn't spawned yet
        # Spawn them outside chunk to prevent movement
        if self.player_spawned is False:
                self.protocol.send_packet("player_position_and_look",
                             self.protocol.buff_type.pack("dddff?", x, y, z,
                                                          viewpoint.get('yaw_256'),
                                                          viewpoint.get('pitch'), 0b00000),
                                    self.protocol.buff_type.pack_varint(0))

                self.player_spawned = True

        if self.is_bedrock:
            return

        # Teleport and spectate viewpoint entity
        if self.viewpoint_spawned is False:
            self.spawn_viewpoint_entity(viewpoint)

            self.viewpoint_spawned = True
        else :
            self.protocol.send_packet('entity_teleport', self.protocol.buff_type.pack_varint(self.viewpoint_id),
                             self.protocol.buff_type.pack("dddbbb",
                                    x,
                                    viewpoint.get('y'),
                                    z,
                                    viewpoint.get('yaw_256'),
                                    viewpoint.get('pitch'),
                                    0))

            self.protocol.send_packet('entity_head_look',
                             self.protocol.buff_type.pack_varint(self.viewpoint_id),
                             self.protocol.buff_type.pack("b", viewpoint.get('yaw_256')))

        if self.viewpoint_used is False:
            self.protocol.send_packet('camera', self.protocol.buff_type.pack_varint(self.viewpoint_id))
            self.viewpoint_used = True

    def send_time(self):
        # Time of day
        self.protocol.send_packet('time_update',
                         self.protocol.buff_type.pack("Qq", 0,
                                             # Cycle
                                             self.current_chunk.time  if self.current_chunk.cycle is True
                                             else (0 - self.current_chunk.time)))

    def next_viewpoint(self):
        if self.is_bedrock:
            return

        count = len(self.current_chunk.viewpoints)

        if count is 0:
            return
        elif self.current_viewpoint < count - 1:
            self.current_viewpoint += 1
            self.send_viewpoint()
        elif voting_mode:
            self.current_viewpoint = 0
            self.send_viewpoint()
        else:
            self.random_chunk()

    def reset_chunk(self):
        self.player_spawned = False
        self.viewpoint_spawned = False
        self.viewpoint_used = False
        self.raining = False

        self.send_respawn()

    def next_chunk(self):
        if len(config.chunks[self.version_name]) > 1:
            index = config.chunks[self.version_name].index(self.current_chunk)
            next_index = index + 1 if index < len(config.chunks[self.version_name]) - 1 else 0
            self.current_chunk = config.chunks[self.version_name][next_index]

        self.reset_chunk()
        self.send_chunk()

    def previous_chunk(self):
        if len(config.chunks[self.version_name]) > 1:
            index = config.chunks[self.version_name].index(self.current_chunk)
            prev_index = index - 1 if index > 0 else len(config.chunks[self.version_name]) - 1
            self.current_chunk = config.chunks[self.version_name][prev_index]

        self.reset_chunk()
        self.send_chunk()

    def random_chunk(self):
        if len(config.chunks[self.version_name]) > 1:
            current_chunk = self.current_chunk

            while current_chunk == self.current_chunk:
                self.current_chunk = random.choice(config.chunks[self.version_name])

        self.reset_chunk()
        self.send_chunk()

    def send_tablist(self):
        self.protocol.send_packet("player_list_header_footer",
                         self.protocol.buff_type.pack_string(json.dumps({
                            "text": "\ue340\uf801\ue341\n\ue342\uf801\ue343"
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

    def send_keep_alive(self):
        self.protocol.send_packet("keep_alive", self.protocol.buff_type.pack("Q", 0))

    @abc.abstractmethod
    def send_join_game(self):
        raise NotImplementedError('users must define send_join_game to use this base class')

    @abc.abstractmethod
    def send_respawn(self):
        raise NotImplementedError('users must define send_respawn to use this base class')

    @abc.abstractmethod
    def spawn_viewpoint_entity(self, viewpoint):
        raise NotImplementedError('users must define spawn_viewpoint_entity to use this base class')

    @abc.abstractmethod
    def send_chat_message(self, message):
        raise NotImplementedError('users must define send_chat_message to use this base class')

    @abc.abstractmethod
    def send_inventory(self):
        raise NotImplementedError('users must define send_inventory to use this base class')
