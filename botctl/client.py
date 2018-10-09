import json
import sys
import operator

from datetime import datetime
from functools import reduce

from botctl.gateway import BotCMSGateway, BotIntegrationsGateway
from botctl.types import BotControlCommand


class BotClient:
    def __init__(self, gateway):
        self._gateway = gateway

    def get_bots(self):
        response = self._gateway.get('/bots')
        return response.json()

    def get_by_name(self, bot_name):
        bots = self.get_bots()
        for bot in bots:
            if bot.get('name') == bot_name:
                users = self.get_bot_users_by_id(bot['id'])
                if users:
                    bot.update({'users': users})

                return bot

    def make_admin(self, bot_id, user_id):
        self.set_user_role(bot_id, user_id, 'admin')

    def remove_admin(self, bot_id, user_id):
        self.set_user_role(bot_id, user_id, 'customer')

    def set_user_role(self, bot_id, user_id, role):
        url = f'/bots/{bot_id}/users/{user_id}'
        self._gateway.put(url, json={'role': role})

    def make_bot(self, bot_name):
        self._gateway.post('/bots', json={'name': bot_name})

    def destroy_bot(self, bot_name):
        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}'
        self._gateway.delete(url)

    def get_bot_users_by_id(self, bot_id):
        url = f'/bots/{bot_id}/users'
        return self._gateway.get(url).json()

    def invite_user(self, bot_name, user_email):
        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')
        url = f'/bots/{bot_id}/invite'
        self._gateway.post(url, json={'email': user_email})

    def invite_user(self, bot_id, user_email):
        url = f'/bots/{bot_id}/invite'
        self._gateway.post(url, json={'email': user_email})

    def uninvite_user(self, bot_id, user_id):
        url = f'/bots/{bot_id}/users/{user_id}'
        self._gateway.delete(url)

    def post_conversation(self, bot_name, conversation):
        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}/conversations'
        response = self._gateway.post(url, data=conversation, fail=False)
        if not response.ok:
            # Now de platform expects the name of the script file
            parsed_conversation = json.loads(conversation)
            time_stamp = datetime.utcnow().timestamp()
            body = {
                'name': f'{time_stamp}-{bot_name}-script.json',
                'script': json.dumps(parsed_conversation)
            }
            response = self._gateway.post(url, json=body)

    def install_bot_integration(self,
                                bot_name,
                                integration_name,
                                integration_config):

        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}/integrations/{integration_name}/install'
        request_body = json.loads(integration_config)
        response = self._gateway.post(url, json=request_body, fail=False)

        if response.status_code == 409:
            url = f'/bots/{bot_id}/integrations/{integration_name}'
            response = self._gateway.put(url, json=request_body)

        if not response.ok:
            sys.stderr.write((f'Could not install {integration_name} '
                              f'integration on bot {bot_name}\n'))

    def install_nlp(self, bot_name, nlp_config):
        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}/nlp_provider/luis'
        response = self._gateway.post(url, json=json.loads(nlp_config))
        if not response.ok:
            print(response.status_code, response.text)


class BotClientCommand(BotControlCommand):
    def set_up(self):
        self.client = BotClient(BotCMSGateway(self.config))

    def dump_bot_name(self, bot):
        print(bot.get('name'))

    def dump_bot(self, bot):
        name = bot['name']
        bot_id = bot['id']
        bot_header = f'name: {name}\nid: {bot_id}\n'
        users = map(
            lambda u: f"- {u['email']} ({u['role']})", bot.get('users', [])
        )
        users_table = '\n'.join(users)

        print(bot_header)
        print(f'Users:\n{users_table}')


class IntegrationClient:
    def __init__(self, gateway):
        self._gateway = gateway

    def get_integration(self, integration_name):
        return self._gateway.get(
            f'/integrations/{integration_name}'
        ).json()

    def get_integrations(self):
        return self._gateway.get(
            '/integrations'
        ).json()

    def get_function(self, integration_name, function_name):
        return self._gateway.get(
            f'/integrations/{integration_name}/functions/{function_name}'
        ).json()

    def call_function(self, integration_name, function_name, args):
        if args:
            function_spec = self.get_function(integration_name, function_name)
            payload = self._build_function_payload(function_spec, args)
            return self._gateway.post(
                f'/integrations/{integration_name}/functions/{function_name}',
                json=payload
            ).json()
        else:
            return self._gateway.post(
                f'/integrations/{integration_name}/functions/{function_name}'
            ).json()


class IntegrationClientCommand(BotControlCommand):
    def set_up(self):
        self.client = IntegrationClient(BotIntegrationsGateway(self.config))

    def _dump_config_options(self, integration):
        options = integration.get('configuration_options')
        if not options:
            return

        print('CONFIGURATION OPTIONS')
        for option, spec in options.items():
            print(f'{option:25}  {spec["description"]}')

    def _dump_function_names(self, integration):
        functions = integration.get('functions')
        if not functions:
            return

        print('\nFUNCTIONS AVAILABLE')
        for function_name in sorted(functions.keys()):
            print(function_name)

    def dump_integration(self, integration):
        self._dump_config_options(integration)
        self._dump_function_names(integration)
