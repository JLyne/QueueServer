import logging
import os
import glob

from yaml import SafeLoader

from queueserver.chunk import Chunk
from queueserver.log import file_handler, console_handler

import yaml

logger = logging.getLogger('config')
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

chunks = {}


def load_chunk_config():
    with open(r'./config.yml') as file:
        entries = yaml.load(file, Loader=SafeLoader)

        for entry in entries:
            name = entry.get('name', 'Untitled')
            contributors = entry.get('contributors', list())
            environment = entry.get('environment', dict())
            folder = entry.get('folder')
            viewpoints = entry.get('viewpoints', list())

            if folder is None:
                logger.error('Entry %s has no folder defined. Skipped.'.format(name))
                continue

            folder_path = os.path.join(os.getcwd(), './packets', folder)

            if os.path.exists(folder_path) is False:
                logger.error('Folder for entry {} does not exist. Skipped.'.format(name))
                continue

            for subfolder in glob.glob(os.path.join(folder_path, '*/')):
                version = os.path.basename(os.path.normpath(subfolder))

                if chunks.get(version) is None:
                    chunks[version] = []

                if chunks.get(version) is not None:
                    chunk = Chunk(name, contributors, environment, folder, version, viewpoints)
                    logger.info('Loaded {} for version {}'.format(chunk.name, version))

                    chunks[version].append(chunk)

        for version in chunks:
            if len(chunks[version]) == 0:
                logger.error('No entries defined for {}'.format(str(version)))
                exit(1)

        return chunks
