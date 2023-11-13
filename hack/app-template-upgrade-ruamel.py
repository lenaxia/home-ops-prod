import argparse
import logging
import os
from copy import deepcopy
from ruamel.yaml import YAML

LOG = logging.getLogger('app-template-upgrade')

class MyDumper(YAML):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def setup_logging():
    LOG.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)

def load_yaml_file(filepath):
    yaml = YAML()
    with open(filepath, 'r') as file:
        return yaml.load(file)

def save_yaml_file(filepath, data):
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(filepath, 'w') as file:
        yaml.dump(data, file)

def load_key(data, path):
    value = data
    for key in path.split('.'):
        value = value.get(key, {})
    return value

def set_key(data, path, value):
    node = data
    split_path = path.split('.')
    index = 0
    while index < len(split_path) - 1:
        key = split_path[index]
        if not node.get(key, None):
            node[key] = {}
        node = node[key]
        index += 1
    node[split_path[index]] = value

def should_process_template(args, filepath, data):
    if args.skip_version_check and load_key(data, 'spec.values.controllers'):
        LOG.info(f'Probably already upgraded as "controllers" key exists, skipping {filepath}')
        return False
    return load_key(data, 'spec.chart.spec.chart') == 'app-template' and load_key(data, 'spec.chart.spec.version') < '2.0.2'

def main():
    parser = argparse.ArgumentParser('app-template-upgrade')
    parser.add_argument('d', help='Directory to scan')
    parser.add_argument('-s', '--skip-version-check', action='store_true', help='Skip app-template version check, checks if key "controllers" exists')
    parser.add_argument('-y', '--yeet', help='YOLO the upgrade and process every template', action='store_true')
    args = parser.parse_args()

    for root, _, files in os.walk(args.d):
        for file in files:
            if file != 'helmrelease.yaml':
                continue
            filepath = os.path.join(root, file)
            try:
                data = load_yaml_file(filepath)
            except Exception as exc:
                LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention')
                continue
            if data['kind'] != 'HelmRelease':
                continue

            if should_process_template(args, filepath, data):
                try:
                    process(filepath, data)
                except Exception as exc:
                    LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention', exc_info=exc)
                    continue

                if not args.yeet:
                    return

# ... [Include all other functions here, unchanged, such as process(), process_controllers(), etc.] ...
import argparse
import logging
import os
from copy import deepcopy
from ruamel.yaml import YAML

LOG = logging.getLogger('app-template-upgrade')

class MyDumper(YAML):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def setup_logging():
    LOG.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    LOG.addHandler(ch)

def load_yaml_file(filepath):
    yaml = YAML()
    with open(filepath, 'r') as file:
        return yaml.load(file)

def save_yaml_file(filepath, data):
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(filepath, 'w') as file:
        yaml.dump(data, file)

def load_key(data, path):
    value = data
    for key in path.split('.'):
        value = value.get(key, {})
    return value

def set_key(data, path, value):
    node = data
    split_path = path.split('.')
    index = 0
    while index < len(split_path) - 1:
        key = split_path[index]
        if not node.get(key, None):
            node[key] = {}
        node = node[key]
        index += 1
    node[split_path[index]] = value

def should_process_template(args, filepath, data):
    if args.skip_version_check and load_key(data, 'spec.values.controllers'):
        LOG.info(f'Probably already upgraded as "controllers" key exists, skipping {filepath}')
        return False
    return load_key(data, 'spec.chart.spec.chart') == 'app-template' and load_key(data, 'spec.chart.spec.version') < '2.0.2'

def main():
    parser = argparse.ArgumentParser('app-template-upgrade')
    parser.add_argument('d', help='Directory to scan')
    parser.add_argument('-s', '--skip-version-check', action='store_true', help='Skip app-template version check, checks if key "controllers" exists')
    parser.add_argument('-y', '--yeet', help='YOLO the upgrade and process every template', action='store_true')
    args = parser.parse_args()

    for root, _, files in os.walk(args.d):
        for file in files:
            if file != 'helmrelease.yaml':
                continue
            filepath = os.path.join(root, file)
            try:
                data = load_yaml_file(filepath)
            except Exception as exc:
                LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention')
                continue
            if data['kind'] != 'HelmRelease':
                continue

            if should_process_template(args, filepath, data):
                try:
                    process(filepath, data)
                except Exception as exc:
                    LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention', exc_info=exc)
                    continue

                if not args.yeet:
                    return

if __name__ == "__main__":
    setup_logging()
    LOG.warning('💣 WARNING! This script may not work for everything, but will put keys into the right spot for the most part...')
    LOG.warning('💣 WARNING! Use at your own risk')
    main()

