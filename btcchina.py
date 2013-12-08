#!/usr/bin/env python
# vim: et ts=4 sts=4 sw=4:
# http://btcchina.org/api-trade-documentation-zh

import time
import hmac
import hashlib
import base64
import httplib
import json


def php_str(v):
    '''convert variable to string like PHP'''

    if v is True:
        return '1'
    if v is False:
        return ''
    if v is None:
        return ''
    if isinstance(v, float) and v == round(v):
        v = int(v)
    return str(v)


class BTCException(Exception):
    def __init__(self, info):
        self.message = info

    def __str__(self):
        return repr(self.message)


class BTCChina():
    def __init__(self, access=None, secret=None):
        self.access_key = access
        self.secret_key = secret

    def _get_tonce(self):
        return int(time.time() * 1000000)

    def _get_params_hash(self, pdict):
        to_hash = []

        # The order of params is critical for calculating a correct hash
        for f in ['tonce', 'accesskey', 'requestmethod',
                  'id', 'method', 'params']:
            if not pdict[f]:
                value = ''
            elif f == 'params':
                value = ','.join([php_str(v) for v in pdict[f]])
            else:
                value = str(pdict[f])

            to_hash.append(f + '=' + value)

        # now with correctly ordered param string, calculate hash
        return hmac.new(self.secret_key,
                        '&'.join(to_hash),
                        hashlib.sha1).hexdigest()

    def _private_request(self, post_data):
        #fill in common header parameters
        tonce = self._get_tonce()
        common_data = {
            'tonce': tonce,
            'accesskey': self.access_key,
            'requestmethod': 'post'}

        # If ID is not passed as a key of post_data, just use tonce, or 1
        if not 'id' in post_data:
            post_data['id'] = tonce

        params_hash = self._get_params_hash(
            dict(post_data.items() + common_data.items()))
        auth = base64.b64encode(self.access_key + ':' + params_hash)

        headers = {
            'Authorization': 'Basic ' + auth,
            'Json-Rpc-Tonce': tonce,
            'Connection': 'Keep-Alive'}

        # post_data dictionary passed as JSON
        conn = httplib.HTTPSConnection("api.btcchina.com")
        conn.request('POST', '/api_trade_v1.php',
                     json.dumps(post_data), headers)
        response = conn.getresponse()

        # check response code, ID, and existence of 'result' or 'error'
        # before passing a dict of results
        if response.status == 200:
            # this might fail if non-json data is returned
            result = response.read()
            try:
                resp_dict = json.loads(result)
            except ValueError:
                raise BTCException('No JSON object is returned: ' + result)

            # The id's may need to be used by the calling application,
            # but for now, check and discard from the return dict.
            # The caller need to check 'result' or 'error'.
            if str(resp_dict['id']) == str(post_data['id']):
                return resp_dict
        else:
            return {'code': response.status, 'message': response.reason}

        return None

    def __getattr__(self, method):
        def function(params=[]):
            post_data = {'method': method, 'params': params}
            result = self._private_request(post_data)
            if 'result' not in result:
                result.update({'params': params})
                raise BTCException(str(result))
            return result['result']
        return function


# buyOrder([price, amount])
# cancelOrder([id])
# getAccountInfo()
# getDeposits([currency, pendingonly])
# getMarketDepth2([limit])
# getOrder([id])
# getOrders([openonly])
# getTransactions([type, limit])
# getWithdrawal([id])
# getWithdrawals([currency, pendingonly])
# requestWithdrawal([currency, amount])
# sellOrder([price, amount])

if __name__ == '__main__':
    from pprint import pprint
    bc = BTCChina('YOUR_ACCESS_KEY',
                  'YOUR_SECRET_KEY')
    pprint(bc.getAccountInfo())
    pprint(bc.getDeposits(['BTC', False]))
    pprint(bc.getMarketDepth2([5]))
    pprint(bc.getOrders([True]))
    pprint(bc.getTransactions())
    pprint(bc.getWithdrawals(['BTC', False]))
