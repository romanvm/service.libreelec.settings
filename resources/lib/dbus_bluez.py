# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2020-present Team LibreELEC

import dbus_utils
import dbussy
import ravel

BUS_NAME = 'org.bluez'
ERROR_REJECTED = 'org.bluez.Error.Rejected'
INTERFACE_ADAPTER = 'org.bluez.Adapter1'
INTERFACE_AGENT = 'org.bluez.Agent1'
INTERFACE_AGENT_MANAGER = 'org.bluez.AgentManager1'
INTERFACE_DEVICE = 'org.bluez.Device1'
PATH_BLUEZ = '/org/bluez'
PATH_AGENT = '/kodi/agent/bluez'


@ravel.interface(ravel.INTERFACE.SERVER, name=INTERFACE_AGENT)
class Agent(object):

    agent = None

    @classmethod
    def register_agent(cls, *args, **kwargs):
        if cls.agent is not None:
            raise RuntimeError('An agent is already registered')
        manager_register_agent()
        cls.agent = cls(*args, **kwargs)
        dbus_utils.BUS.request_name(
            BUS_NAME, flags=dbussy.DBUS.NAME_FLAG_DO_NOT_QUEUE)
        dbus_utils.BUS.register(
            path=PATH_AGENT, interface=cls.agent, fallback=True)
        return cls.agent

    @ravel.method(
        in_signature='os',
        out_signature='',
        arg_keys=['device', 'uuid']
    )
    def AuthorizeService(self, device, uuid):
        self.authorize_service(device, uuid)

    @ravel.method(
        in_signature='',
        out_signature=''
    )
    def Cancel(self):
        self.cancel()

    @ravel.method(
        in_signature='ouq',
        out_signature='',
        arg_keys=['device', 'passkey', 'entered']
    )
    def DisplayPasskey(self, device, passkey, entered):
        self.display_passkey(device, passkey, entered)

    @ravel.method(
        in_signature='os',
        out_signature='',
        arg_keys=['device', 'pincode']
    )
    def DisplayPinCode(self, device, pincode):
        self.display_pincode(device, pincode)

    @ravel.method(
        in_signature='',
        out_signature=''
    )
    def Release(self):
        raise NotImplementedError

    @ravel.method(
        in_signature='o',
        out_signature='',
        arg_keys=['device']
    )
    def RequestAuthorization(self, device):
        self.request_authorization(device)

    @ravel.method(
        in_signature='ou',
        out_signature='',
        arg_keys=['device', 'passkey']
    )
    def RequestConfirmation(self, device, passkey):
        self.request_confirmation(device, passkey)

    @ravel.method(
        in_signature='o',
        out_signature='u',
        arg_keys=['device'],
        result_keyword='reply'
    )
    def RequestPasskey(self, device):
        passkey = self.request_passkey(device)
        reply[0] = (dbus.Signature('u'), passkey)

    @ravel.method(
        in_signature='o',
        out_signature='s',
        arg_keys=['device'],
        result_keyword='reply'
    )
    def RequestPinCode(self, device, reply):
        pincode = self.request_pincode(device)
        reply[0] = (dbus.Signature('s'), pincode)

    def reject(self, message):
        raise dbus.DBusError(ERROR_REJECTED, message)


def get_managed_objects():
    return dbus_utils.call_method(BUS_NAME, '/', dbussy.DBUSX.INTERFACE_OBJECT_MANAGER, 'GetManagedObjects')


def adapter_get_property(path, name):
    return dbus_utils.call_method(BUS_NAME, path, dbussy.DBUS.INTERFACE_PROPERTIES, 'Get', INTERFACE_ADAPTER, name)


def adapter_get_powered(path):
    return adapter_get_property(path, 'Powered')


def adapter_remove_device(path, device):
    return dbus_utils.call_method(BUS_NAME, path, INTERFACE_ADAPTER, 'RemoveDevice', device)


def adapter_set_property(path, name, value):
    return dbus_utils.call_method(BUS_NAME, path, dbussy.DBUS.INTERFACE_PROPERTIES, 'Set', INTERFACE_ADAPTER, name, value)


def adapter_set_alias(path, alias):
    return adapter_set_property(path, 'Alias', (dbussy.DBUS.Signature('s'), alias))


def adapter_set_powered(path, powered):
    return adapter_set_property(path, 'Powered', (dbussy.DBUS.Signature('b'), powered))


def adapter_start_discovery(path):
    return dbus_utils.call_method(BUS_NAME, path, INTERFACE_ADAPTER, 'StartDiscovery')


def adapter_stop_discovery(path):
    return dbus_utils.call_method(BUS_NAME, path, INTERFACE_ADAPTER, 'StopDiscovery')


def device_get_property(path, name):
    return dbus_utils.call_method(BUS_NAME, path, dbussy.DBUS.INTERFACE_PROPERTIES, 'Get', INTERFACE_DEVICE, name)


def device_get_connected(path):
    return device_get_property(path, 'Connected')


def device_connect(path):
    return dbus_utils.run_method(BUS_NAME, path, INTERFACE_DEVICE, 'Connect')


def device_disconnect(path):
    return dbus_utils.call_method(BUS_NAME, path, INTERFACE_DEVICE, 'Disconnect')


def device_pair(path):
    return dbus_utils.run_method(BUS_NAME, path, INTERFACE_DEVICE, 'Pair')


def device_set_property(path, name, value):
    return dbus_utils.call_method(BUS_NAME, path, dbussy.DBUS.INTERFACE_PROPERTIES, 'Set', INTERFACE_DEVICE, name, value)


def device_set_trusted(path, trusted):
    return device_set_property(path, 'Trusted', (dbussy.DBUS.Signature('b'), trusted))


def manager_register_agent():
    return dbus_utils.call_method(BUS_NAME, PATH_BLUEZ, INTERFACE_AGENT_MANAGER, 'RegisterAgent', PATH_AGENT, 'KeyboardDisplay')


def find_adapter():
    if system_has_bluez():
        objects = get_managed_objects()
        for path, interfaces in objects.items():
            if interfaces.get(INTERFACE_ADAPTER):
                return path


def find_devices():
    devices = {}
    objects = get_managed_objects()
    for path, interfaces in objects.items():
        if interfaces.get(INTERFACE_DEVICE):
            devices[path] = interfaces[INTERFACE_DEVICE]
    return devices


def system_has_bluez():
    return BUS_NAME in dbus_utils.list_names()
