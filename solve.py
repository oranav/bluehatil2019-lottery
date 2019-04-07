#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 Oranav <contact@oranav.me>
#
# Distributed under terms of the GPLv3 license.
import argparse
import time
import base64
import urllib.parse
import requests
import sys
import json
from itertools import count
from hashpumpy import hashpump

parser = argparse.ArgumentParser()
parser.add_argument('payment_token')
parser.add_argument('-n', '--name', default='oranav')
parser.add_argument('-s', '--server-url', default='http://localhost:8080')
args = parser.parse_args()


# Generate a guess blob
numbers = [1,2,3,4,5,6]
guess = {}
guess['guess'] = numbers
guess['name'] = args.name
guess['timestamp'] = int(time.time())

guess_blob = urllib.parse.urlencode(guess).encode('latin1')
guess_b64 = base64.urlsafe_b64encode(guess_blob)
payment_blob, payment_mac = args.payment_token.split('.')
params = {'guess_blob': guess_b64,
          'payment_blob': payment_blob,
          'payment_mac': payment_mac }

resp = requests.get("%s/sign" % args.server_url, params=params)
mac_b64 = resp.text
try:
    mac = base64.urlsafe_b64decode(mac_b64)
    if len(mac) != 20:
        raise Exception()
except Exception:
    print('Guess generation error: %s' % mac_b64)
    sys.exit(1)
print('Guess blob: %r' % guess_blob)
print('Guess MAC: %r' % mac)


# Find key length
for key_length in count(1):
    print('Trying key length %d...' % key_length, end=' ')
    newmac_hex, newmsg = hashpump(mac.hex(), guess_blob, '&', key_length)
    newmac = bytes.fromhex(newmac_hex)
    newmsg_b64 = base64.urlsafe_b64encode(newmsg)
    newmac_b64 = base64.urlsafe_b64encode(newmac)
    params = {'guess_blob': newmsg_b64, 'guess_mac': newmac_b64}
    # For dramatization effects
    time.sleep(0.2)
    resp = requests.get('%s/verify' % args.server_url, params=params)
    print(resp.text)
    if resp.text == 'Verified':
        break
print('Key length is %d' % key_length)


# Wait for lottery
print('Wait for lottery please.')
winnings_blob_b64 = input('Enter winnings blob: ')
winnings_mac_b64 = input('Enter winnings signature: ')

# Extract numbers from winning blob
winnings_blob = base64.urlsafe_b64decode(winnings_blob_b64)
winnings = dict(urllib.parse.parse_qsl(winnings_blob.decode("latin1")))
numbers.clear()
numbers.extend(json.loads(winnings['winning_numbers']))
print('Winning numbers: %r' % numbers)


# Pump the hash
new_guess_blob = urllib.parse.urlencode(guess).encode('latin1')
append = b'&' + new_guess_blob
newmac_hex, newmsg = hashpump(mac.hex(), guess_blob, append, key_length)
newmac = bytes.fromhex(newmac_hex)
newmsg_b64 = base64.urlsafe_b64encode(newmsg)
newmac_b64 = base64.urlsafe_b64encode(newmac)
print('New guess blob: %r' % newmsg)
print('New MAC: %r' % newmac)

print('New guess blob (B64): %r' % newmsg_b64)
print('New MAC (B64): %r' % newmac_b64)


# Verify the new blob
print('Verifying...', end=' ')
params = {'guess_blob': newmsg_b64, 'guess_mac': newmac_b64}
print(requests.get('%s/verify' % args.server_url, params=params).text)


# Certify
print('Certifying...')
params.update({'winnings_blob': winnings_blob_b64,
               'winnings_mac': winnings_mac_b64})
resp = requests.get('%s/certify' % args.server_url, params=params)
cert_b64 = resp.text
print('Cert (B64): %r' % cert_b64)


# Make sure we won!
print('Making sure we won...', end=' ')
params = {'winner': base64.urlsafe_b64encode(args.name.encode('latin1')),
          'certification': cert_b64}
print(requests.get('%s/verify-certification' % args.server_url, params=params)
      .text)
