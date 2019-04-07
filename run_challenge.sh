#! /bin/sh
#
# run.sh
# Copyright (C) 2019 Oranav <contact@oranav.me>
#
# Distributed under terms of the GPLv3 license.
#

generate_key() {
    exec 2>/dev/null;
    dd if=/dev/urandom bs=1 count=12 | base64;
}

signing_key="$(generate_key)"
winning_key="$(generate_key)"
certification_key="$(generate_key)"
payment_key="$(generate_key)"
duration=300

echo "Signing key:" "$signing_key"
echo "Winning key:" "$winning_key"
echo "Certification key:" "$certification_key"
echo "Payment key:" "$payment_key"
echo "Duration:" "$duration"
echo

base="$(dirname "$0")"

sudo docker run --rm --name redis -p 6379:6379 -d redis

"$base/env/bin/python3" "$base/bottle_server.py" --signing_key "$signing_key" --winning_key "$winning_key" --certification_key "$certification_key" --payment_key "$payment_key" --duration "$duration"
