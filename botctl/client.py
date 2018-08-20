import json
import sys

from botctl.gateway import BotCMSGateway
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
                return bot

    def make_bot(self, bot_name):
        self._gateway.post('/bots', json={'name': bot_name})

    def post_conversation(self, bot_name, conversation):
        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}/conversations'
        self._gateway.post(url, data=conversation)

    def install_bot_integration(self,
                                bot_name,
                                integration_name,
                                integration_config):

        bot = self.get_by_name(bot_name)
        bot_id = bot.get('id')

        url = f'/bots/{bot_id}/integrations/{integration_name}/install'
        request_body = json.loads(integration_config)
        response = self._gateway.post(url, json=request_body)

        if response.status_code == 409:
            url = f'/bots/{bot_id}/integrations/{integration_name}'
            response = self._gateway.put(url, json=request_body)

        if not response.ok:
            sys.stderr.write((f'Could not install {integration_name} '
                              f'integration on bot {bot_name}\n'))


class BotClientCommand(BotControlCommand):
    def set_up(self):
        self.client = BotClient(BotCMSGateway(self.config))

    def dump_bot_name(self, bot):
        print(bot.get('name'))

    def dump_bot(self, bot):
        print(json.dumps(bot, indent=2))
