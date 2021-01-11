#!/usr/bin/env python
# coding=utf-8

import logging

from cinderclient import client
import novaclient.client as nvclient
# import glanceclient.client as glclient


OS_IDENTITY_API_VERSION = 3
OS_AUTH_URL = "http://{XXXXXX}/v3"
OS_PROJECT_DOMAIN_NAME = "Default"
OS_USER_DOMAIN_NAME = "Default"
OS_PROJECT_NAME = "admin"
OS_TENANT_NAME = "admin"
OS_USERNAME = "admin"
OS_PASSWORD = "*****************"
OS_REGION_NAME = "RegionOne"
OS_INTERFACE = "internal"
OS_ENDPOINT_TYPE = "internal"
OS_CACERT = "/**/ssl/certs/ca-certificates.crt"


class CinderAPI:
    def __init__(self, version=2, username=OS_USERNAME, api_key=OS_PASSWORD, project_id=OS_PROJECT_NAME, auth_url=OS_AUTH_URL):
        self.client = None
        self.client = client.Client(version=version,
                                    username=username,
                                    api_key=api_key,
                                    project_id=project_id,
                                    auth_url=auth_url,
                                    http_log_debug=False
                                    )
                                    # cacert=CACERT,
                                    # endpoint_type=ENDPOINT_TYPE)

    def volume_create(self, size, name, volume_type="volumes_ceph", snapshot_id=None, image_id=None):
        data = {'name': name,
                'volume_type': volume_type,
                'snapshot_id': snapshot_id,
                'imageRef': image_id
                }

        volume = self.client.volumes.create(size, **data)

        return volume.id

    def volume_delete(self, volume_id):
        return self.client.volumes.delete(volume_id)

    def volume_type_list(self):
        return self.client.volume_types.list()

    def volumes_list(self):
        return self.client.volumes.list()

    def volume_get(self, volume_id):
        volume_data = self.client.volumes.get(volume_id)
        return volume_data

    def volume_snapshots_list(self, volume_id):
        fileds = {
            'volume_id': volume_id
        }
        snapshots = self.client.volume_snapshots.list(search_opts=fileds)
        return snapshots

    def volume_snapshot_del(self, snapshot):
        return self.client.volume_snapshots.delete(snapshot)

    def volume_snapshot_create(self, volume_id, name):
        return self.client.volume_snapshots.create(volume_id=volume_id, force=True, name=name)


# class GlanceAPI:
#     def __init__(self, version=2, username=OS_USERNAME, api_key=OS_PASSWORD, project_id=OS_PROJECT_NAME,
#                  auth_url=OS_AUTH_URL):
#         self.client = None
#         self.client = glclient.Client(version=version,
#                                       endpoint="http://198.28.32.10:9292",
#                                       username=username,
#                                       password=api_key,
#                                       project_id=project_id,
#                                       auth_url=auth_url,
#                                       os_region_name=OS_REGION_NAME,
#                                       http_log_debug=True)
#
#     def list_all_images(self):
#         return self.client.images.list()
#

class NovaAPI:
    def __init__(self, version=2, username=OS_USERNAME, api_key=OS_PASSWORD, project_id=OS_PROJECT_NAME, auth_url=OS_AUTH_URL):
        self.client = None
        try:
            self.client = nvclient.Client(version=version,
                                          username=username,
                                          password=api_key,
                                          project_name=project_id,
                                          project_domain_name=OS_PROJECT_DOMAIN_NAME,
                                          auth_url=auth_url,
                                          http_log_debug=False,
                                          endpoint_type=OS_ENDPOINT_TYPE,
                                          user_domain_name=OS_USER_DOMAIN_NAME)
        except TypeError:
            self.client = nvclient.Client(version=version,
                                          username=username,
                                          api_key=api_key,
                                          project_id=project_id,
                                          auth_url=auth_url,
                                          http_log_debug=False)

    def instance_volume_attach(self, volume_id, instance_id, device):
        return self.client.volumes.create_server_volume(instance_id, volume_id, device)

    def instance_volume_detach(self, instance_id, volume_id):
        return self.client.volumes.delete_server_volume(instance_id, volume_id)

    def instance_volumes_list(self, instance_id):
        volumes = self.client.volumes.get_server_volumes(instance_id)
        return volumes

    def create_vm_instance(self, vm_nam, image, flavor, zone='nova', nics=[]):
        instance = self.client.servers.create(name=vm_nam, image=image, flavor=flavor, nics=nics,
                                              availability_zone=zone)
        return instance.id

    def get_instance_status(self, instance_uuid, networks):
        ins_info = self.client.servers.get(instance_uuid)
        res = [ins_info.status]
        for net in networks:
            if net in ins_info.addresses and len(ins_info.addresses[net]) > 0:
                ip = ins_info.addresses[net][0]['addr']
                res.append(ip)

        return res

    def network_list(self, networks):
        nets = {}
        try:
            all_nets = self.client.networks.list()
            for net in all_nets:
                if net.label in networks:
                    nets[net.label] = net.id
        except:
            for n_nam in networks:
                net = self.client.neutron.find_network(n_nam)
                nets[net.name] = net.id

        return nets

    def flavor_list(self):
        flavors = self.client.flavors.list()
        _flavor_dict = {}
        for f in flavors:
            _flavor_dict[f.name] = {
                'id': f.id,
                'ram': f.ram,
                'vcpus': f.vcpus,
                'disk': f.disk
            }

        return _flavor_dict

    def image_list(self):
        try:
            images = self.client.images.list()
        except Exception:
            images = self.client.glance.list()

        _images_dict = {}
        for image in images:
            _images_dict[image.name] = image.id

        return _images_dict


# if __name__ == "__main__":
#     logging.basicConfig(format='[%(asctime)s][%(levelname)s]:%(message)s', level=logging.DEBUG)
#     # log = logging.getLogger(__name__)
#     log = logging.getLogger("fanwen")
#     log.debug("cinder test.....")

    # ca = CinderAPI()
    # print ca.volumes_list()
    # print ca.volume_type_list()
    # print ca.volume_create(2, "fanwen-test", volume_type="standard-iops")

    # na = NovaAPI()
    # print na.flavor_list()
    # print na.image_list()
    # print na.network_list()
