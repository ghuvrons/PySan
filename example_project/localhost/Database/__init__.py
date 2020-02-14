import PySan.Database.MySQL as MySQL

databases = {}
databases["vpn_radius"] = MySQL.db({
        "host": "citrapay.com",
        "user": "ghuvrons",
        "password": "Gg104986",
        "database": "radius_vpn",
    })

def close():
    myclient.close()