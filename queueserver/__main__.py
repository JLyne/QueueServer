import os
import sys

from argparse import ArgumentParser

from quarry.net.server import ServerFactory
from twisted.internet import reactor

from queueserver.config import load_chunk_config
from queueserver.log import logger
from queueserver.prometheus import init_prometheus
from queueserver.protocol import Protocol, build_versions

if getattr(sys, 'frozen', False):  # PyInstaller adds this attribute
    # Running in a bundle
    path = os.path.join(sys._MEIPASS, 'queueserver')
else:
    # Running in normal Python environment
    path = os.path.dirname(__file__)

parser = ArgumentParser()
parser.add_argument("-a", "--host", default="127.0.0.1", help="bind address")
parser.add_argument("-p", "--port", default=25567, type=int, help="bind port")
parser.add_argument("-m", "--max", default=65535, type=int, help="player count")
parser.add_argument("-r", "--metrics", default=None, type=int, help="expose prometheus metrics on specified port")
parser.add_argument("-s", "--voting", type=str,
                    help="Enables voting mode with the given secret. Shows entry counts and prev/next buttons.")
parser.add_argument("-b", "--bungeecord", action='store_true', help="Enables bungeecord forwarding support")
parser.add_argument("-v", "--velocity", default=None, type=str,
                    help="enable velocity modern forwarding support with the given secret")

args = parser.parse_args()

server_factory = ServerFactory()
server_factory.protocol = Protocol
server_factory.max_players = args.max
server_factory.motd = "Queue Server"
server_factory.online_mode = False
server_factory.compression_threshold = 5646848

metrics_port = args.metrics

if args.bungeecord is True and args.velocity is True:
    logger.error("Cannot use both bungeecord and velocity forwarding at the same time.")
    exit(1)

if args.velocity is True:
    logger.info('Enabling Velocity forwarding support')

if args.bungeecord is True:
    logger.info('Enabling Bungeecord forwarding support')

load_chunk_config()
build_versions()

if metrics_port is not None:
    init_prometheus(metrics_port)

Protocol.voting_mode = args.voting is not None
Protocol.voting_secret = args.voting
Protocol.bungee_forwarding = args.bungeecord
Protocol.velocity_forwarding = args.velocity is not None
Protocol.velocity_forwarding_secret = args.velocity

server_factory.listen(args.host, args.port)
logger.info('Server started')
logger.info("Listening on {}:{}".format(args.host, args.port))
reactor.run()
