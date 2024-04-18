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
    #if args.skip_version_check:
    #    LOG.info(f'Probably already upgraded as "controllers" key exists, skipping {filepath}')
    #    return False
    return load_key(data, 'spec.chart.spec.chart') == 'app-template' and load_key(data, 'spec.chart.spec.version') < '3.2.0'


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
    ingress_values = new_helm_values.pop('ingress', None)
    if ingress_values is not None:
        new_helm_values['ingress'] = process_ingress(ingress_values, data)

    # Update service
    service_values = new_helm_values.pop('service', None)
    if service_values is not None:
        new_helm_values['service'] = process_service(service_values, data)

    # Update persistence
    persistence_values = new_helm_values.pop('persistence', None)
    if persistence_values is not None:
        new_helm_values['persistence'] = process_persistence(persistence_values, data)

    # Update controllers
    controller_values = new_helm_values.pop('controller', None)
    if controller_values is not None:
        new_helm_values['controllers'] = process_controllers(controller_values, data)

    # Update initContainers
    if init_containers_values := new_helm_values.pop('initContainers', None):
        for init_container_name, init_container_value in init_containers_values.items():
            set_key(new_helm_values, f'controllers.main.initContainers.{init_container_name}', process_init_container(init_container_value))

    new['spec']['values'] = set_key_order(new_helm_values)
    LOG.info(f"Replacing Original file: {filepath}")
    save_yaml_file(filepath, new)


def process_controllers(data, full_data):
    return {
        'main': data
    }


def process_ingress(data, full_data):
    ingress_main = data.pop('main', None)
    if ingress_main is None:
        return data

    service_identifiers = {
        svc['name']: svc for svc in full_data.get('service', {}).values()
    }

    ingress_main['hosts'] = [
        {
            'host': host_data.get('host'),
            'paths': [
                {
                    'path': path_data.get('path'),
                    'pathType': path_data.get('pathType'),
                    'service': {
                        'identifier': path_data.get('service', {}).get('name', 'main'),
                        'port': path_data.get('service', {}).get('port')
                    },
                } for path_data in host_data.get('paths', [])
            ],
        } for host_data in ingress_main.get('hosts', [])
    ]

    for host in ingress_main['hosts']:
        for path in host['paths']:
            service = path['service']
            if service['identifier'] in service_identifiers:
                service_obj = service_identifiers[service['identifier']]
                service['identifier'] = service_obj['identifier'] if 'identifier' in service_obj else service_obj['name']
            else:
                service['identifier'] = 'main'

    data['main'] = ingress_main
    return data


def process_service(data, full_data):
    controllers = full_data.get('controllers', {})
    processed_data = {}

    for service_name, service_data in data.items():
        primary = service_data.pop('primary', False)
        ports = service_data.pop('ports', {})
        processed_ports = {}
        for port_name, port_settings in ports.items():
            processed_ports[port_name] = {
                'port': port_settings['port'],
                'enabled': port_settings.get('enabled', True),
            }

        service_data['ports'] = processed_ports
        service_data['primary'] = primary

        if 'controller' not in service_data:
            controller_name = service_data.get('controller', 'main')
            if controller_name in controllers:
                service_data['controller'] = controller_name
            elif 'main' in controllers:
                service_data['controller'] = 'main'
            elif 'app' in controllers:
                service_data['controller'] = 'app'
            else:
                # Return data unmodified if neither 'main' nor 'app' controllers are found
                return data

        processed_data[service_name] = service_data

    return processed_data



def process_persistence(data, full_data):
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


def process_init_container(data, full_data):
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
