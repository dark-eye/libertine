# Copyright 2017 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import dbus

from . import utils


class Client(object):
    def __init__(self):
        self._get_manager()

    def _get_manager(self):
        self._manager = None

        try:
            from .service.manager import LIBERTINE_MANAGER_NAME, LIBERTINE_MANAGER_OBJECT
            if utils.set_session_dbus_env_var():
                bus = dbus.SessionBus()
                self._manager = bus.get_object(LIBERTINE_MANAGER_NAME, LIBERTINE_MANAGER_OBJECT)
                self._interface = LIBERTINE_MANAGER_NAME
        except ImportError as e:
            utils.get_logger().warning("Libertine service libraries not installed.")
        except dbus.exceptions.DBusException as e:
            utils.get_logger().warning("Exception raised while discovering d-bus service: {}".format(str(e)))

    def _do_operation(self, operation):
        # It's possible that the service has gone down from when first getting the object.
        # This catches the dbus excpetion if it did, and tries to reconnect to the service
        # and then retry the dbus method.
        while self.valid:
            try:
                return operation()
            except dbus.exceptions.DBusException as e:
                self._get_manager()
        else:
            return False

    @property
    def valid(self):
        return self._manager is not None

    def container_operation_start(self, id):
        retries = 0
        while not self._do_operation(lambda: self._manager.get_dbus_method('container_operation_start', self._interface)(id)):
            retries += 1
            if retries > 5:
                return False
            time.sleep(.5)

        return True

    def container_operation_finished(self, id, app_name, pid):
        return self._do_operation(lambda: self._manager.get_dbus_method("container_operation_finished", self._interface)(id, app_name, pid))

    def container_stopped(self, id):
        return self._do_operation(lambda: self._manager.get_dbus_method('container_stopped', self._interface)(id))
