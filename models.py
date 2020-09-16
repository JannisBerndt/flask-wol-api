from app import db

class Preset(db.Model):
    __tablename__ = "presets"

    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String())
    ip_or_hostname = db.Column(db.String())
    port = db.Column(db.Integer)
    secureon = db.Column(db.String())

    def __init__(self, mac_address, ip_or_hostname, port, secureon):
        self.mac_address = mac_address
        self.ip_or_hostname = ip_or_hostname
        self.port = port
        self.secureon = secureon

    def serialize(self):
        return {
            "id": self.id,
            "mac_address": self.mac_address,
            "ip_or_hostname": self.ip_or_hostname,
            "port": self.port,
            "secureon": self.secureon
        }
