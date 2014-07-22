#
# ovirt-engine-setup -- ovirt engine setup
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""Connection plugin."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-engine-dwh')


from otopi import constants as otopicons
from otopi import transaction
from otopi import util
from otopi import plugin


from ovirt_engine_setup.dwh import constants as odwhcons
from ovirt_engine_setup.engine_common import database
from ovirt_engine_setup.engine_common \
    import constants as oengcommcons


@util.export
class Plugin(plugin.PluginBase):
    """Connection plugin."""

    class DBTransaction(transaction.TransactionElement):
        """yum transaction element."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("DWH database Transaction")

        def prepare(self):
            pass

        def abort(self):
            connection = self._parent.environment[odwhcons.DBEnv.CONNECTION]
            if connection is not None:
                connection.rollback()
                self._parent.environment[odwhcons.DBEnv.CONNECTION] = None

        def commit(self):
            connection = self._parent.environment[odwhcons.DBEnv.CONNECTION]
            if connection is not None:
                connection.commit()

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _commands(self):
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            self.DBTransaction(self)
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        name=odwhcons.Stages.DB_CONNECTION_CUSTOMIZATION,
        condition=lambda self: self.environment[odwhcons.CoreEnv.ENABLE],
        before=(
            oengcommcons.Stages.DB_OWNERS_CONNECTIONS_CUSTOMIZED,
        ),
        after=(
            oengcommcons.Stages.DIALOG_TITLES_S_DATABASE,
        ),
    )
    def _customization(self):
        dbovirtutils = database.OvirtUtils(
            plugin=self,
            dbenvkeys=odwhcons.Const.DWH_DB_ENV_KEYS,
        )
        dbovirtutils.getCredentials(
            name='DWH',
            queryprefix='OVESETUP_DWH_DB_',
            defaultdbenvkeys=odwhcons.Const.DEFAULT_DWH_DB_ENV_KEYS,
            show_create_msg=True,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        condition=lambda self: self.environment[odwhcons.CoreEnv.ENABLE],
        before=(
            oengcommcons.Stages.DIALOG_TITLES_E_DATABASE,
        ),
        after=(
            oengcommcons.Stages.DIALOG_TITLES_S_DATABASE,
            oengcommcons.Stages.DB_OWNERS_CONNECTIONS_CUSTOMIZED,
        ),
    )
    def _engine_customization(self):
        dbovirtutils = database.OvirtUtils(
            plugin=self,
            dbenvkeys=odwhcons.Const.ENGINE_DB_ENV_KEYS,
        )
        dbovirtutils.getCredentials(
            name='Engine',
            queryprefix='OVESETUP_ENGINE_DB_',
            defaultdbenvkeys={
                'host': '',
                'port': '5432',
                'secured': '',
                'hostValidation': False,
                'user': 'engine',
                'password': None,
                'database': 'engine',
            },
            show_create_msg=False,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        name=odwhcons.Stages.DB_CONNECTION_AVAILABLE,
        condition=lambda self: self.environment[odwhcons.CoreEnv.ENABLE],
        after=(
            odwhcons.Stages.DB_SCHEMA,
        ),
    )
    def _connection(self):
        self.environment[
            odwhcons.DBEnv.STATEMENT
        ] = database.Statement(
            environment=self.environment,
            dbenvkeys=odwhcons.Const.DWH_DB_ENV_KEYS,
        )
        # must be here as we do not have database at validation
        self.environment[
            odwhcons.DBEnv.CONNECTION
        ] = self.environment[odwhcons.DBEnv.STATEMENT].connect()


# vim: expandtab tabstop=4 shiftwidth=4