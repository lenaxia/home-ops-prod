import argparse
import logging
import os
from copy import deepcopy
from ruamel.yaml import YAML

LOG = logging.getLogger('app-template-upgrade')

helmReleaseNames = ["helmrelease.yaml", "helm-release.yaml"]


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


def should_process(args, filepath, data):
    if args.skip_version_check and load_key(data, 'spec.values.controllers'):
        LOG.info(f'Probably already upgraded as "controllers" key exists, skipping {filepath}')
        return False
    return load_key(data, 'spec.chart.spec.chart') == 'app-template' and load_key(data, 'spec.chart.spec.version') < '3.1.0'


def main():
    parser = argparse.ArgumentParser('app-template-upgrade')
    parser.add_argument('d', help='Directory to scan')
    parser.add_argument('-s', '--skip-version-check', action='store_true', help='Skip app-template version check, checks if key "controllers" exists')
    parser.add_argument('-y', '--yeet', help='YOLO the upgrade and process every template', action='store_true')
    args = parser.parse_args()

    for root, _, files in os.walk(args.d):
        for file in files:
            if file not in helmReleaseNames:
                continue
            filepath = os.path.join(root, file)
            try:
                data = load_yaml_file(filepath)
            except Exception as exc:
                LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention')
                LOG.error(f'{exc}')
                continue
            if data['kind'] != 'HelmRelease':
                continue

            if should_process(args, filepath, data):
                try:
                    process(filepath, data)
                except Exception as exc:
                    LOG.error(f'failed to process: {filepath}, script is not good enough - will need manual intervention', exc_info=exc)
                    LOG.error(f'{exc}')
                    continue
                if not args.yeet:
                    return


def process(filepath, data):
    new = deepcopy(data)
    new['spec']['chart']['spec']['version'] = '3.1.0'
    helm_values = new['spec'].pop('values')
    new_helm_values = deepcopy(helm_values)

    # Update ingress
    if ingress_values := new_helm_values.pop('ingress', None):
        set_key(new_helm_values, 'ingress', process_ingress(ingress_values))

    # Update service
    if service_values := new_helm_values.pop('service', None):
        set_key(new_helm_values, 'service', process_service(service_values))

    # Update persistence
    if persistence_values := new_helm_values.pop('persistence', None):
        set_key(new_helm_values, 'persistence', process_persistence(persistence_values))

    # Update controllers
    if controller_values := new_helm_values.pop('controller', None):
        set_key(new_helm_values, 'controllers', process_controllers(controller_values))

    # Update initContainers
    if init_containers_values := new_helm_values.pop('initContainers', None):
        for init_container_name, init_container_value in init_containers_values.items():
            set_key(new_helm_values, f'controllers.main.initContainers.{init_container_name}', process_init_container(init_container_value))

    new['spec']['values'] = set_key_order(new_helm_values)
    LOG.info(f"Replacing Original file: {filepath}")
    save_yaml_file(filepath, new)


def process_controllers(data):
    # The provided values.yaml does not specify a transformation for controllers,
    # so we assume that the existing structure is already compliant.
    # If a transformation is needed, the logic should be implemented here.
    return data


def process_ingress(data):
    ingress_main = data.pop('main', None)
    if ingress_main is None:
        return data

    ingress_main['hosts'] = [{
        'paths': [{
            'path': '/',
            'pathType': 'Prefix',
            'backend': {
                'service': {
                    'name': ingress_main.get('serviceName', ''),
                    'port': {
                        'number': int(port.get('port', 80))
                    }
                }
            }
            }] for port in ingress_main.pop('ports', [])
        }]
    }]
        }]
    } for port in ingress_main.pop('ports', [])]

    data['main'] = ingress_main
    return data


def process_service(data):
    service_main = data.pop('main', None)
    if service_main is None:
        return data

    # Assuming the new schema requires a 'controller' key under 'service.main'
    if 'controller' not in service_main:
        service_main['controller'] = 'default'  # or whatever the default controller should be

    ports = service_main.pop('ports', [])
    service_main['ports'] = {}
    for port in ports:
        service_main['ports'][port['name']] = {
            'port': port['port'],
            'enabled': True,
            'primary': port.get('primary', False)
        }

    # Update service.main to include additional keys as per the provided values.yaml
    service_main['type'] = service_main.get('type', 'ClusterIP')
    service_main['externalTrafficPolicy'] = service_main.get('externalTrafficPolicy', '')
    service_main['ipFamilyPolicy'] = service_main.get('ipFamilyPolicy', '')
    service_main['ipFamilies'] = service_main.get('ipFamilies', [])
    service_main['annotations'] = service_main.get('annotations', {})
    service_main['labels'] = service_main.get('labels', {})
    service_main['extraSelectorLabels'] = service_main.get('extraSelectorLabels', {})

    data['main'] = service_main
    return data


def process_persistence(data):
    for persistence_name, persistence_values in data.items():
        if persistence_values.get('enabled') is False:
            continue
        if 'readOnly' in persistence_values:
            persistence_values.pop('readOnly')
        if mount_path := persistence_values.pop('mountPath', None):
            persistence_values['globalMounts'] = [{
                'path': mount_path
            }]
            if sub_path := persistence_values.pop('subPath', None):
                persistence_values['globalMounts'][0]['subPath'] = sub_path
    return data


def process_init_container(data):
    image = data.get('image')

    # Check if image is a string and needs processing
    if isinstance(image, str):
        image_split = image.split(':', 1)
        if len(image_split) == 2:
            data['image'] = {
                'repository': image_split[0],
                'tag': image_split[1],
            }
        else:
            LOG.error(f'Image format incorrect, expected "repository:tag", got: {image}')
    # Check if image is a map with 'repository' and 'tag'
    elif isinstance(image, dict):
        if 'repository' not in image or 'tag' not in image:
            LOG.error('Image is incorrectly formatted. Expected keys "repository" and "tag"')
    else:
        LOG.error(f'Unexpected image data type: {type(image).__name__}')

    if 'volumeMounts' in data:
        data.pop('volumeMounts')

    return data


def set_key_order(data):
    order = ['defaultPodOptions', 'controllers', 'service', 'ingress', 'persistence']
    new_data = {}
    for key in order:
        if key in data:
            new_data[key] = data.pop(key)
    new_data.update(data)
    return new_data


if __name__ == "__main__":
    setup_logging()
    LOG.warning('💣 WARNING! This script may not work for everything, but will put keys into the right spot for the most part...')
    LOG.warning('💣 WARNING! Use at your own risk')
    main()
