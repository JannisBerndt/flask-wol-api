from flask import Blueprint, request
from flask_cors import cross_origin
import socket, re, json, hashlib
from app import app
from models import Preset
import logging

logging.basicConfig(level=logging.DEBUG)

bp = Blueprint('wol', __name__, url_prefix='/wol')

@bp.route('/wake', methods=['POST'])
@cross_origin()
def wake():
    errors = ""
    try:
        mac_address = request.form.get('mac-address').upper()
        dst_ip = request.form.get('ip-address')
        dst_port = request.form.get('port')
        secureOn = str(request.form.get('secureon'))
        app.logger.info("MAC: " + mac_address + ", IP: " + dst_ip + ", Port: " + dst_port + ", Password: " + secureOn)

        if len(secureOn) != 6:
            errors += "The SecureOn password has to be 6 characters long."
        preset = Preset.query.filter_by(secureOn=secureOn).all()
        if len(preset) > 1:
            return json.dumps({
                    'message': "The given password returns multiple presets!"
                }), 400
        preset = preset[0] if preset else None
        app.logger.info(preset)
        if preset is not None:
            mac_address = preset["mac_address"]
            dst_ip = preset["ip_or_hostname"]
            dst_port = preset["port"]
        else:
            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_address) is None:
                errors += "Invalid Mac Address. You need 12 Hex numbers and 5 colons. "
            if not "".join(dst_ip.split('.')).isnumeric():
                try:
                    dst_ip = socket.gethostbyname(dst_ip)
                except:
                    errors += "Unable to resolve Hostname."
            dst_port = int(dst_port)
            if not -1 < dst_port < 65536 :
                errors += "Invalid Port. Port has to be between 0 and 65535. "
            if errors != "":
                return json.dumps({
                    'message': errors
                }), 400
        secureOn = secureOn.encode('ASCII').hex()
        print(dst_ip, dst_port)
        mac_address = "".join(mac_address.split(':'))
        packetData = "FFFFFFFFFFFF" + "".join([mac_address]*16) + secureOn
        print(packetData)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytearray.fromhex(packetData), (dst_ip, dst_port))
    except Exception as e:
        print(e)
        errors += "Something went wrong. Please make sure you provided 1. a MAC Address with 6 blocks of two hex numbers separated by colons, 2. a valid IP address in dotted decimal notation or a hostname of you choice and 3. a port between 0 and 65535. Optionally you can also provide a secureOn password, which has to be 6 characters long."
        return json.dumps({
            'message': errors
        }), 400
    return json.dumps({
            'message': 'Magic Packet successfully sent.'
        }), 200
