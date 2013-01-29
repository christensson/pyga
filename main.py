#!/usr/bin/python3

import argparse
import logging

import log
import ctrl

def createParser():
    parser = argparse.ArgumentParser(description='Python photo gallery')
    parser.add_argument(
        '-v,', '--verbose', dest='verbosity',
        action='count', default=0,
        help='Enable verbosity')
    parser.add_argument(
        '-l', '--log', dest='log_file',
        action='store', type=str, default=None,
        help='Log file')
    parser.add_argument(
        '-d', '--dir', dest='dir_list',
        action='append', type=str, required=True,
        help='Directory to search for photos')
    parser.add_argument(
        '-c', '--config', dest='config_file',
        action='store', type=str, default='config.json',
        help='Use config file [default=%(default)s]')
    return parser


def main():
    parser = createParser()
    args = parser.parse_args()

    log.init('root', args.verbosity, args.log_file)
    logger = logging.getLogger('root')
    logger.info('Python photo gallery started!')
    logger.debug('Args: %s', str(args))

    controller = ctrl.Controller(args)
    controller.main()

if __name__ == "__main__":
    main()
