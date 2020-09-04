from flask import Blueprint, request
from flask_cors import cross_origin
import socket, re, json, hashlib
from . import db

bp = Blueprint('wol', __name__, url_prefix='/wol')

@bp.route('/wake', methods=['POST'])
@cross_origin()
def wake():
    mac_address = request.form.get('mac-address').upper()
    dst_ip = request.form.get('ip-address')
    dst_port = int(request.form.get('port'))
    secureOn = request.form.get('secureon')
    preset = db.query_db("SELECT * FROM presets WHERE secureOn = ?", [secureOn], True)
    if preset is not None:
        print("Triggered")
        mac_address = preset["mac_address"]
        dst_ip = preset["ip_or_hostname"]
        dst_port = preset["port"]
    errors = ""
    print(dst_ip, dst_port)
    secureOn = secureOn.encode('ASCII').hex()
    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_address) is None:
        errors += "Invalid Mac Address. You need 12 Hex numbers and 5 colons.\n"
    if not "".join(dst_ip.split('.')).isnumeric():
        try:
            dst_ip = socket.gethostbyname(dst_ip)
        except:
            errors += "Unable to resolve Hostname."
    if not -1 < dst_port < 65536 :
        errors += "Invalid Port. Port has to be between 0 and 65535.\n"
    if errors != "":
        return json.dumps({
            'message': errors
        }), 400
    print(dst_ip, dst_port)
    mac_address = "".join(mac_address.split(':'))
    packetData = "FFFFFFFFFFFF" + "".join([mac_address]*16) + secureOn
    print(packetData)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytearray.fromhex(packetData), (dst_ip, dst_port))
    return json.dumps({
            'message': 'Magic Packet successfully sent.'
        }), 200
