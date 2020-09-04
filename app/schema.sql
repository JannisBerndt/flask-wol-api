DROP TABLE IF EXISTS presets;

CREATE TABLE presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL,
    ip_or_hostname TEXT NOT NULL,
    port INTEGER NOT NULL,
    secureOn TEXT NOT NULL
);