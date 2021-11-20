import abc
import random
import time
from pathlib import Path

from quarry.types.uuid import UUID

from queueserver.protocol import Protocol, voting_mode, voting_secret
from queueserver.config import chunks
from queueserver.voting import entry_json, entry_navigation_json

parent_folder = Path(__file__).parent.parent


class Version(object, metaclass=abc.ABCMeta):
    protocol_version = None
    chunk_format = None

    def __init__(self, protocol: Protocol, bedrock: False):
        self.protocol = protocol
        self.viewpoint_id = 999
        self.viewpoint_uuid = UUID.random()

        self.current_chunk = None
        self.current_viewpoint = None
        self.raining = False

        self.player_spawned = False
        self.viewpoint_spawned = False
        self.viewpoint_used = False

        self.last_click = time.time()

        self.is_bedrock = bedrock

    def player_joined(self):
        self.send_join_game()

        if voting_mode:
            self.current_chunk = chunks[self.chunk_format][0]
        else:
            self.current_chunk = random.choice(chunks[self.chunk_format])

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
            self.send_reset_world()

        self.current_viewpoint = 0
        self.send_viewpoint()

        # Chunk packets
        for packet in self.current_chunk.packets:
            self.protocol.send_packet(packet.get('type'), packet.get('packet'))

        # Start/stop rain as necessary
        self.send_weather(self.current_chunk.weather == 'rain')

        if self.is_bedrock:  # Current versions of geyser seem to ignore the time sometimes. Send repeatedly for now.
            self.protocol.ticker.add_loop(100, self.send_time)
        else:
            self.send_time()

        if voting_mode:
            self.send_chat_message(entry_json(
                chunks[self.chunk_format].index(self.current_chunk) + 1,
                                          len(chunks[self.chunk_format])))
        # Credits
        self.send_chat_message(self.current_chunk.credit_json())

        if voting_mode and not self.is_bedrock:
            self.send_chat_message(entry_navigation_json(self.protocol.uuid, voting_secret))

    def send_viewpoint(self):
        viewpoint = self.current_chunk.viewpoints[self.current_viewpoint]
        x = viewpoint.get('x')
        z = viewpoint.get('z')
        y = viewpoint.get('y')

        # Player hasn't spawned yet
        # Spawn them outside chunk to prevent movement
        if self.player_spawned is False:
            self.send_spawn()
            self.player_spawned = True

        if self.is_bedrock:
            return

        # Teleport and spectate viewpoint entity
        if self.viewpoint_spawned is False:
            self.spawn_viewpoint_entity(viewpoint)

            self.viewpoint_spawned = True
        else:
            self.protocol.send_packet('entity_teleport', self.protocol.buff_type.pack_varint(self.viewpoint_id),
                                      self.protocol.buff_type.pack("dddbbb", x, y, z,
                                                                   viewpoint.get('yaw_256'), viewpoint.get('pitch'), 0))

            self.protocol.send_packet('entity_head_look',
                                      self.protocol.buff_type.pack_varint(self.viewpoint_id),
                                      self.protocol.buff_type.pack("b", viewpoint.get('yaw_256')))

        if self.viewpoint_used is False:
            self.protocol.send_packet('camera', self.protocol.buff_type.pack_varint(self.viewpoint_id))
            self.viewpoint_used = True

    def next_viewpoint(self):
        if self.is_bedrock:
            return

        count = len(self.current_chunk.viewpoints)

        if count == 0:
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
        if len(chunks[self.chunk_format]) > 1:
            index = chunks[self.chunk_format].index(self.current_chunk)
            next_index = index + 1 if index < len(chunks[self.chunk_format]) - 1 else 0
            self.current_chunk = chunks[self.chunk_format][next_index]

        self.reset_chunk()
        self.send_chunk()

    def previous_chunk(self):
        if len(chunks[self.chunk_format]) > 1:
            index = chunks[self.chunk_format].index(self.current_chunk)
            prev_index = index - 1 if index > 0 else len(chunks[self.chunk_format]) - 1
            self.current_chunk = chunks[self.chunk_format][prev_index]

        self.reset_chunk()
        self.send_chunk()

    def random_chunk(self):
        if len(chunks[self.chunk_format]) > 1:
            current_chunk = self.current_chunk

            while current_chunk == self.current_chunk:
                self.current_chunk = random.choice(chunks[self.chunk_format])

        self.reset_chunk()
        self.send_chunk()

    @abc.abstractmethod
    def send_join_game(self):
        raise NotImplementedError('send_join_game must be defined to use this base class')

    @abc.abstractmethod
    def send_spawn(self):
        raise NotImplementedError('send_spawn must be defined to use this base class')

    @abc.abstractmethod
    def send_respawn(self):
        raise NotImplementedError('send_respawn must be defined to use this base class')

    @abc.abstractmethod
    def send_reset_world(self):
        raise NotImplementedError('send_reset_world must be defined to use this base class')

    @abc.abstractmethod
    def send_keep_alive(self):
        raise NotImplementedError('send_keep_alive must be defined to use this base class')

    @abc.abstractmethod
    def spawn_viewpoint_entity(self, viewpoint):
        raise NotImplementedError('spawn_viewpoint_entity must be defined to use this base class')

    @abc.abstractmethod
    def get_viewpoint_entity_type(self):
        raise NotImplementedError('get_viewpoint_entity_type must be defined to use this base class')

    @abc.abstractmethod
    def send_time(self):
        raise NotImplementedError('send_time must be defined to use this base class')

    @abc.abstractmethod
    def send_weather(self, rain=False):
        raise NotImplementedError('send_weather must be defined to use this base class')

    @abc.abstractmethod
    def send_chat_message(self, message):
        raise NotImplementedError('send_chat_message must be defined to use this base class')

    @abc.abstractmethod
    def send_tablist(self):
        raise NotImplementedError('send_tablist must be defined to use this base class')

    @abc.abstractmethod
    def send_inventory(self):
        raise NotImplementedError('send_inventory must be defined to use this base class')
