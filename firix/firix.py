'''
firix api library. contains abstraction to the firi.no api

This file is deveoped by Kim Timothy Engh for use with the
cryto exchange firi.com.

firix is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

firix is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser
General Public LICENSE along with firix. If not, see
<http://www.gnu.org/licenses/lgpl-3.0.txt> and
<http://www.gnu.org/licenses/gpl-3.0.txt>.
'''

import requests
import hmac
import hashlib
import json


class FXRequests:
    HOST = 'https://api.firi.com'
    VALIDITY = 500
    
    def __init__(self, client_id, secret_key):
        self.__client_id = client_id
        self.__secret_key = secret_key

    @classmethod
    def epoch(cls):
        response = cls.get_public('/time')
        payload = response.json()
        return payload["time"]

    @classmethod
    def get_public(cls, url: str, params: dict|None = None, headers: dict|None = None):
        params = {} if params is None else params
        headers = {} if headers is None else headers

        return requests.get(url=cls.HOST + url, params=params, headers=headers)

    def sign(self, epoch, validity, message):
        """Adds the required HMAC data to the params and headers dictionary.
        The given dictionaries are mutated inplace."""

        message_copy = message.copy()
        message_copy.update(timestamp=str(epoch), validity=str(validity))
        message_json = json.dumps(message_copy, separators=(',', ':')).encode()

        signature = (hmac.new(
            key=self.__secret_key.encode(),
            msg=message_json,
            digestmod=hashlib.sha256)).hexdigest()
        
        return signature

    def get(self, url, params: dict|None = None, headers: dict|None = None):
        epoch = self.epoch()
        validity = self.VALIDITY
        client_id = self.__client_id

        params = {} if params is None else params
        params.update(timestamp=epoch, validity=validity)
        
        signature = self.sign(epoch, validity, params)

        headers = {} if headers is None else headers
        headers.update({
            'firi-user-clientid': client_id,
            'firi-user-signature': signature})

        return requests.get(url=self.HOST + url, params=params, headers=headers)

    def post(self, url, body: dict|None = None, headers: dict|None = None):
        epoch = self.epoch()
        validity = self.VALIDITY
        client_id = self.__client_id

        body = {} if body is None else body
        signature = self.sign(epoch, validity, body)

        params = {'timestamp': epoch, 'validity': validity}
        
        headers = {} if headers is None else headers
        headers.update({
            'firi-user-clientid': client_id,
            'firi-user-signature': signature})

        return requests.post(url=self.HOST + url, json=body, params=params, headers=headers)

    def delete(self, url, params: dict|None = None, headers: dict|None = None):
        epoch = self.epoch()
        validity = self.VALIDITY
        client_id = self.__client_id

        params = {} if params is None else params
        params.update(timestamp=epoch, validity=validity)
        
        signature = self.sign(epoch, validity, params)

        headers = {} if headers is None else headers
        headers.update({
            'firi-user-clientid': client_id,
            'firi-user-signature': signature})
        
        return requests.delete(url=self.HOST + url, params=params, headers=headers)    


class FXBalance:
    def __init__(self, fxr: FXRequests):
        self.fxr = fxr

    def wallets(self):
        response = self.fxr.get('/v2/balances')


class FXCoin:
    def __init__(self, fxr: FXRequests):
        self.fxr = fxr
    
    def pending_withdraw(self, coin: str):
        response = self.fxr.get(f'/v2/{coin}/withdraw/pending')
        return response

    def users_address(self, coin: str):
        response = self.fxr.get(f'/v2/{coin}/address')
        return response


class FXDeposit:
    def __init__(self, fxr: FXRequests):
        self.fxr = fxr

    def history(self, count: int, before: int):
        params = {'count': count, 'before': before}
        
        response = self.fxr.get('/v2/deposit/history', params=params)
        return response

    def address(self):
        response = self.fxr.get('/v2/deposit/address')


class FXHistory:    
    @staticmethod
    def transactions(year: str|None = None, month: str|None = None, count: int|None = None):
        match year, month:
            case str(), str():
                url = f'/v2/history/transactions/{month}/{year}'

            case str(), None:
                url = f'/v2/history/transactions/{year}'

            case None, None:
                url = f'/v2/history/transactions'

            case None, str():
                raise ValueError('If month is given, year must be given.')

            case _:
                raise ValueError('No match for given paramters')

        params = {'count': count} if not count is None else {}
        response = FXRequests.get_public(url, params=params)
        return response

    @staticmethod
    def market(market: str, count: int|None = None):
        params = {'count': count} if not count is None else {}
        response = FXRequests.get_public(f'/v2/history/{market}', params=params)
        return response


class FXMarket:
    @staticmethod
    def ticker(market: str):
        response = FXRequests.get_public(f'/v2/markets/{market}/ticker')
        return response

    @staticmethod
    def availible_tickers():
        response = FXRequests.get_public('/v2/markets/tickers')
        return response

    @staticmethod
    def availible_markets():
        response = FXRequests.get_public('/v2/markets')
        return response

    @staticmethod
    def market_info(market: str):
        response = FXRequests.get_public(f'/v2/markets/{market}')
        return response

    @staticmethod
    def order_books(market: str):
        response = FXRequests.get_public(f'/v2/markets/{market}/depth')
        return response      

    @staticmethod
    def history(market: str, count: int|None  = None):
        params = {'count': count} if not count is None else {}
        response = FXRequests.get_public(f'/v2/markets/{market}/depth')
        return response   


class FXOrder:
    def __init__(self, fx: FXRequests):
        self.fxr = fx

    def create(self, market: str, order_type: str, price: str, amount: str):
        body = {'market': market, 'type': order_type, 'price': price, 'amount': amount}
        response = self.fxr.post('/v2/orders', body=body)
        return response

    def delete(self, orderid: int|None = None, market: str|None = None):
        match orderid, market:
            case int(), str():
                url = f'/v2/orders/{orderid}/{market}/detailed'
            
            case int(), None:
                url = f'/v2/orders{orderid}/detailed'

            case None, str():
                url = f'/v2/orders/{market}'

            case None, None:
                url = '/v2/orders'

            case _:
                raise ValueError('No match for given paramters')

        response = self.fxr.delete(url)        
        return response

    def get(self, market: str|None = None, count: int|None = None, history: bool = False):
        match market, history:
            case str(), False:
                url = f'/v2/orders/{market}'

            case None, False:
                url = '/v2/orders'

            case str(), True:
                url = f'/v2/orders/{market}/history'

            case None, True:
                url = '/v2/orders/history'

            case _:
                raise ValueError('No match for given paramters')

        params = {'count': count} if not count is None else {}
        response = self.fxr.get(url, params=params)
        return response

    def get_by_id(self, order_id: int):
        response = self.fxr.get(f'/v2/order/{order_id}')
        return response


class FiriX(FXRequests):
    history = FXHistory
    market = FXMarket
    
    def __init__(self, client_id, secret_key):
        super().__init__(client_id, secret_key)

        self.order = FXOrder(self)
        self.deposit = FXDeposit(self)
        self.balance = FXBalance(self)
        self.coin = FXCoin(self)

