from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import socket, re, json, hashlib
from app import app, db
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
        ip_or_hostname = str(request.form.get('ip-or-hostname'))
        dst_port = int(request.form.get('port')) if request.form.get('port') else None
        secureon = str(request.form.get('secureon'))
        app.logger.info("MAC: " + mac_address + ", IP or Hostname: " + ip_or_hostname + ", Port: " + str(dst_port) + ", Password: " + secureon)
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': 'Unable to parse input data!'
        }), 400

    try:
        if mac_address and ip_or_hostname and dst_port:
            errors += validateMACAddress(mac_address)
            if "".join(ip_or_hostname.split('.')).isnumeric():
                errors += validateIPAddress(ip_or_hostname)
            errors += validatePort(dst_port)
            if secureon and len(secureon) != 6:
                errors += "The SecureOn password has to be 6 characters long."
            if errors:
                return json.dumps({
                    'message': errors
                }), 400
        else:
            return json.dumps({
                'message': 'You are missing some important information. Please either provide a valid MAC Adress, IP and Port or a secureOn password with nothing else.'
            }), 400
        sendMagicPacket(mac_address, ip_or_hostname, port, secureon)
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': e.args
        }), 400
    return json.dumps({
            'message': 'Magic Packet successfully sent.'
        }), 200

@bp.route('/wakepreset', methods=['POST'])
@cross_origin()
def wake_from_preset():
    try:
        name = str(request.form.get('name'))
        secureon = str(request.form.get('secureon'))
        app.logger.info("Name: " + name + ", Password: " + secureon)
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': 'Unable to parse input data!'
        }), 400

    if len(secureon) != 6:
        return json.dumps({
            'message': "The secureOn password has to be 6 characters long."
        }), 400
    preset = Preset.query.filter_by(secureon=secureon, name=name).all()
    if len(preset) > 1:
        return json.dumps({
            'message': "The given name and password belong to multiple presets! This is not allowed."
        }), 400
    preset = preset[0] if preset else None
    if preset is None:
        return json.dumps({
            'message': "The given name password do not match any preset! Please provide a correct name and password."
        }), 400

    try:
        sendMagicPacket(preset.mac_address, preset.ip_or_hostname, preset.port, secureon)
    except Exception as e:
        return json.dumps({
            'message': e.args
        }), 400
    return json.dumps({
        'message': 'Magic Packet successfully sent.'
    }), 200

@bp.route('/add', methods=['POST'])
@cross_origin()
def add_preset():
    errors = ""
    try:
        mac_address = str(request.form.get('mac-address').upper())
        dst_ip = str(request.form.get('ip-or-hostname'))
        dst_port = int(request.form.get('port')) if request.form.get('port') else None
        secureon = str(request.form.get('secureon'))
        name = str(request.form.get('name'))
        app.logger.info("MAC: " + mac_address + ", IP: " + dst_ip + ", Port: " + str(dst_port) + ", Password: " + secureon)
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': 'Unable to parse input data!'
        }), 400
    
    if mac_address and dst_ip and dst_port and secureon:
        errors += validateMACAddress(mac_address)
        errors += validatePort(dst_port)
        if secureon and len(secureon) != 6:
            errors += "The SecureOn password has to be 6 characters long."
        if errors:
            return json.dumps({
                'message': errors
            }), 400
    else:
        return json.dumps({
            'message': 'You are missing some important information. Please provide a valid MAC Adress, IP, Port and secureOn password to create a new preset.'
        }), 400
    
    try:
        preset = Preset(mac_address, dst_ip, dst_port, secureon, name)
        db.session.add(preset)
        db.session.commit()
        return json.dumps({
            'message': "New preset successfully added."
        }), 200
    except Exception as e:
        app.logger.error(e)
        return json.dumps({
            'message': 'Unable to create this new preset! Please check you input data.'
        }), 400

def validateMACAddress(mac_address):
    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_address) is None:
        return "Invalid Mac Address. You need 12 Hex numbers and 5 colons. "
    return ""

def validateIPAddress(ip_address):
    # RegEx from https://www.oreilly.com/library/view/regular-expressions-cookbook/9780596802837/ch07s16.html
    if re.match(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip_address) is None:
        return "Invalid IP Address. Please use dottet decimal notation with numbers in the IPv4 range. "
    return ""

def validatePort(port):
    if not -1 < port < 65536 :
        return "Invalid Port. Port has to be between 0 and 65535. "
    return ""

def sendMagicPacket(mac_address, ip_or_hostname, port, secureon=""):
    ip = ip_or_hostname
    if not "".join(ip_or_hostname.split('.')).isnumeric():
        try:
            ip = socket.gethostbyname(ip_or_hostname)
        except Exception as e:
            app.logger.error(e)
            raise Exception('Unable to resolve Hostname.')
    try:
        secureon = secureon.encode('ASCII').hex()
        mac_address = "".join(mac_address.split(':'))
        packetData = "FFFFFFFFFFFF" + "".join([mac_address]*16) + secureon
        app.logger.info(packetData)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytearray.fromhex(packetData), (ip, port))
    except Exception as e:
        app.logger.error(e)
        raise Exception('Something went wrong when sending your Magic Packet.')
    return 'Magic Packet successfully sent.'
