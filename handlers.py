# coding: UTF-8
import json
from datetime import datetime, timedelta
from functools import partial

from tornado import gen
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from tornado.httpclient import AsyncHTTPClient

from constants import OPERATIONS_DIRECTION, CURRENCY_URL
from myexceptions import OperationException


class MainHandler(RequestHandler):
    """ Main page """

    def get(self):
        """ Return html """
        self.render("templates/main.html")


class OperationsWebSocket(WebSocketHandler):
    """ Class for working with operations """
    all_packages = []

    def open(self):
        """ open websocket """
        print("WebSocket opened")

    def on_message(self, message):
        """ getting websocket message """
        try:
            data = self.parse_data(message)
            if data.get('method') != 'get_balances':
                url = CURRENCY_URL.format(data.get('date'))
                self.asynchronous_fetch_currency(url, partial(self.check_or_save, data))
            else:
                self.get_balance(data)
        except OperationException as e:
            self.write_message(str(e))

    def on_close(self):
        """ close websocket """
        print("WebSocket closed")

    def get_balance(self, data):
        """ Return balance to client """
        summ = sum([pack['amt_eur'] * OPERATIONS_DIRECTION[pack['method']] for pack in self.all_packages if
                    pack['account'] == data['account']])
        self.write_message('Your balance={} EUR'.format(summ))

    def check_or_save(self, data, currencies):
        """
        Check sum of transfers and balance to perform operation. After success save it

        :param data:
        :param currencies:
        :return:
        """
        data['amt_eur'] = round(data['amt'] / currencies['rates'].get(data['ccy'], 1), 2)
        self.check_transfer_limit(data)
        self.check_balance(data)
        self.all_packages.append(data)
        self.write_message('Success')

    @gen.coroutine
    def asynchronous_fetch_currency(self, url, fn_callback):
        """
        Get currency rate

        :param url: String
        :param fn_callback: Function
        """
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(url)
        try:
            fn_callback(json.loads(response.body.decode('UTF-8')))
        except OperationException as e:
            self.write_message(str(e))
        raise gen.Return(response.body)

    def parse_data(self, message):
        """ Parse and validate imput data """
        data = json.loads(message)
        if not data.get('amt') or not data.get('date') or \
                (not data.get('account') and data.get('method') != 'transfer') or \
                (data.get('method') == 'transfer' and ((not data.get('from_account') or not data.get('to_account')) or
                                                        data.get('from_account') == data.get('to_account'))):
            raise OperationException('Check your input data')
        data['amt'] = float(data['amt'])
        data['date_date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if data['method'] == 'transfer':
            data['account'] = data['from_account']
        return data

    def check_transfer_limit(self, data):
        """ Check limit 10000 and raise if limit exceeeded """
        if data['method'] == 'transfer':
            summ_transfer = sum([pack['amt_eur'] for pack in self.all_packages if pack['account'] == data['account'] and
                                 data['date_date'] - timedelta(days=5) <= pack['date_date'] <= data['date_date'] and
                                 pack['method'] == 'transfer'])
            if summ_transfer + data['amt_eur'] > 10000:
                raise OperationException('You exceeded the limit')

    def check_balance(self, data):
        """ Check remain on balance to perform operation """
        remain = sum([pack['amt_eur'] * OPERATIONS_DIRECTION[pack['method']] for pack in self.all_packages
                      if pack['account'] == data['account'] and
                      data['method'] in ['transfer', 'deposit', 'withdrawal']])
        if remain + OPERATIONS_DIRECTION[data['method']] * data['amt_eur'] < 0:
            raise OperationException('You havent money to perform this operation')
