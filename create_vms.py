#!/usr/bin/env python
# coding=utf-8

# Copyright (C) 2020 - All Rights Reserved
# auth: Fanwen
# mail: fanwen390922198@qq.com


import time

from openstack_api import *
import logging

VM_NUMBERS = 3
VM_NAME_PREFIX = "ceph_test"
IMAGE_NAME = "ubuntu-16.04"
FLAVOR_NAME = "m1.large"
NETWORK = ["admin-internal"]
AVAIL_ZONE = 'nova'

SAS_VOLUME_TYPE = "volume-sas"
SAS_VOLUME_SIZE = 2     # G

SSD_VOLUME_TYPE = "volume-ssd"
SSD_VOLUME_SIZE = 2     # G


class CreateTestVM:
    def __init__(self, log=None):
        self.log = log
        self.na = NovaAPI()
        self.ca = CinderAPI()
        self.images = []
        self.flavors = []
        self.nets = []
        self.instances = []

        self._load_base_data()

    def _load_base_data(self):
        self.images = self.na.image_list()
        self.flavors = self.na.flavor_list()
        self.nets = self.na.network_list(NETWORK)

    def create_vms(self):
        self.log.info("create vm instance...")
        nics = []
        for n_nam in NETWORK:
            nics.append({
                'net-id': self.nets[n_nam]
            })

        for i in range(1, VM_NUMBERS+1):
            vm_nam = "{}-{}".format(VM_NAME_PREFIX, i)
            try:
                uuid = self.na.create_vm_instance(vm_nam=vm_nam,
                                                  image=self.images[IMAGE_NAME],
                                                  flavor=self.flavors[FLAVOR_NAME]['id'],
                                                  nics=nics,
                                                  zone=AVAIL_ZONE)
                self.instances.append(
                    {
                        "name": vm_nam,
                        "instance_uuid": uuid,
                        "ready": False,
                        "usable": True,
                        "ip": None
                    }
                )
                self.log.info("create {} success!".format(vm_nam))
            except Exception, e:
                self.log.error("create {} failed!".format(vm_nam))

    def wait_all_ready(self):
        self.log.info("waitting all instances to be actived....")
        all_waits = len(self.instances)
        while True:
            for ins in self.instances:
                if not ins["ready"] and ins["usable"]:
                    status = self.na.get_instance_status(ins['instance_uuid'], NETWORK)
                    self.log.info("{} statatus is：{}".format(ins['name'], status[0]))
                    if status[0] == "ERROR":
                        ins['usable'] = False
                        all_waits -= 1
                    elif status[0] == "ACTIVE":
                        ins['ready'] = True
                        if len(status) > 1:
                            ins['ip'] = status[1]
                        all_waits -= 1

            if all_waits == 0:
                break

            time.sleep(5)

    def attach_volume_for_every_vm(self):
        self.log.info("create volume and attach to instance....")
        for ins in self.instances:
            if ins["ready"] and ins["usable"]:
                dev_start = 'c'

                if SSD_VOLUME_TYPE is not None:
                    ssd_dev_nam = "{}_ssd_vd{}".format(ins["name"], dev_start)
                    self.log.info("create ssd volume: {}".format(ssd_dev_nam))
                    ssd_volume_id = self.ca.volume_create(size=SSD_VOLUME_SIZE,
                                                          volume_type=SSD_VOLUME_TYPE,
                                                          name=ssd_dev_nam)

                    ssd_device = "/dev/vd{}".format(dev_start)
                    dev_start = chr(ord(dev_start) + 1)

                if SAS_VOLUME_TYPE is not None:
                    sas_dev_nam = "{}_sas_vd{}".format(ins["name"], dev_start)
                    self.log.info("create ssd volume: {}".format(sas_dev_nam))
                    sas_volume_id = self.ca.volume_create(size=SAS_VOLUME_SIZE,
                                                          volume_type=SAS_VOLUME_TYPE,
                                                          name=sas_dev_nam)

                    sas_device = "/dev/vd{}".format(dev_start)

                self.log.info("waitting volumes to be ready!")
                time.sleep(20)

                if SSD_VOLUME_TYPE is not None:
                    self.na.instance_volume_attach(volume_id=ssd_volume_id,
                                                   instance_id=ins['instance_uuid'],
                                                   device=ssd_device)

                    self.log.info("attach {} to instance [{}] as {}".format(ssd_dev_nam, ins['name'], ssd_device))

                if SAS_VOLUME_TYPE is not None:
                    self.na.instance_volume_attach(volume_id=sas_volume_id,
                                                   instance_id=ins['instance_uuid'],
                                                   device=sas_device)

                    self.log.info("attach {} to instance [] as {}".format(sas_dev_nam, ins['name'], sas_device))

    def create_test_enviorment(self):
        self.create_vms()
        self.wait_all_ready()
        self.attach_volume_for_every_vm()

        for ins in self.instances:
            self.log.info("{}   {}".format(ins["ip"], ins["name"]))


if __name__ == "__main__":
    logging.basicConfig(format='[%(asctime)s][%(levelname)s]:%(message)s', level=logging.DEBUG)
    log = logging.getLogger(__name__)

    ct = CreateTestVM(log)
    ct.create_test_enviorment()

