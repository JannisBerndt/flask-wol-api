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
        mac_address = str(request.form.get('mac-address').upper())
        dst_ip = str(request.form.get('ip-address'))
        dst_port = int(request.form.get('port')) if request.form.get('port') else None
        secureOn = str(request.form.get('secureon'))
        app.logger.info("MAC: " + mac_address + ", IP: " + dst_ip + ", Port: " + str(dst_port) + ", Password: " + secureOn)
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': 'Unable to parse input data!'
        }), 400

    try:
        # Use presets only if the password is the only given value. Else, every value apart from the optional secureOn has to be specifid. Otherwise its an error.
        if not mac_address and not dst_ip and not dst_port and secureOn:
            if len(secureOn) != 6:
                return json.dumps({
                    'message': "The SecureOn password has to be 6 characters long."
                }), 400
            preset = Preset.query.filter_by(secureon=secureOn).all()
            if len(preset) > 1:
                return json.dumps({
                        'message': "The given password belongs to multiple presets! This is not allowed."
                    }), 400
            preset = preset[0] if preset else None
            if preset is None:
                return json.dumps({
                        'message': "The given password does not match any preset! Please provide a correct password or all the information needed to send a packet without a preset."
                    }), 400
            #app.logger.info('Preset: ' + preset)
            mac_address = preset.mac_address
            dst_ip = preset.ip_or_hostname
            dst_port = preset.port
            if not "".join(dst_ip.split('.')).isnumeric():
                try:
                    dst_ip = socket.gethostbyname(dst_ip)
                except:
                    errors += "Unable to resolve Hostname. "
        elif mac_address and dst_ip and dst_port:
            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_address) is None:
                errors += "Invalid Mac Address. You need 12 Hex numbers and 5 colons. "
            if not "".join(dst_ip.split('.')).isnumeric():
                try:
                    dst_ip = socket.gethostbyname(dst_ip)
                except:
                    errors += "Unable to resolve Hostname. "
            # RegEx from https://www.oreilly.com/library/view/regular-expressions-cookbook/9780596802837/ch07s16.html
            elif re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', dst_ip) is None:
                errors += "Invalid IP Address. Please use dottet decimal notation with numbers in the IPv4 range. "
            if not -1 < dst_port < 65536 :
                errors += "Invalid Port. Port has to be between 0 and 65535. "
            if secureOn and len(secureOn) != 6:
                errors += "The SecureOn password has to be 6 characters long."
            if errors:
                return json.dumps({
                    'message': errors
                }), 400
        else:
            return json.dumps({
                'message': 'You are missing some important information. Please either provide a valid MAC Adress, IP and Port or a secureOn password with nothing else.'
            }), 400

        secureOn = secureOn.encode('ASCII').hex()
        mac_address = "".join(mac_address.split(':'))
        packetData = "FFFFFFFFFFFF" + "".join([mac_address]*16) + secureOn
        app.logger.info(packetData)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytearray.fromhex(packetData), (dst_ip, dst_port))
    except Exception as e:
        app.logger.error(e)
        errors += "Something went wrong. Please make sure you provided 1. a MAC Address with 6 blocks of two hex numbers separated by colons, 2. a valid IP address in dotted decimal notation or a hostname of you choice and 3. a port between 0 and 65535. Optionally you can also provide a secureOn password, which has to be 6 characters long."
        return json.dumps({
            'message': errors
        }), 400
    return json.dumps({
            'message': 'Magic Packet successfully sent.'
        }), 200
