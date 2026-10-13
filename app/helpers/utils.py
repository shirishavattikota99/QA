import os


def getMongoDbUri(nodeEnv, appClient, partnerId):
    mongoDbUri = ''
    normalized_env = (nodeEnv or "development").strip().lower()
    normalized_client = (appClient or "CORE").strip().upper()

    if normalized_env == 'production':
        if normalized_client == '3XE':
            mongoDbUri = os.getenv('3XE_LIVE_MONGO_URI')
        else:
            mongoDbUri = os.getenv('LIVE_MONGO_URI')
    else:
        if normalized_client == '3XE':
            mongoDbUri = os.getenv('3XE_DEV_MONGO_URI')
        else:
            mongoDbUri = os.getenv('DEV_MONGO_URI')
    # if not found
    if not mongoDbUri:
        raise Exception('Not able to find database URI')

    # replace db name
    db_name = get_db_name(partnerId)
    if "{DB_NAME}" in mongoDbUri:
        mongoDbUri = mongoDbUri.replace("{DB_NAME}", db_name)

    return mongoDbUri


def get_db_name(partnerId):
    normalized_partner_id = (partnerId or "").strip().upper()

    switcher = {
        # shar local
        '28C134': "casino_db",
        # core dev
        '523875': "betz_db",
        'DB9A8F': "winnerslots_db",
        'E42D7D': "magical_db",
        'C8726B': "ultimajackpot_db",
        '3C29E2': "blocspinz_db",
        '01E436': "jackpotvilla_db",
        'B1994A': "slotobet_db",
        '4D5B30': "priva_db",
        'AAB290': "playmondial_db",
        'D00E64': "bongospin_db",
        # core prod
        '1C43B1': "betz_db",
        '6C9671': "winnerslots_db",
        'E186C3': "magical_db",
        '775A7E': "priva_db",
        '719C0C': "playmondial_db",
        '38BB71': "bongospin_db",
        '55AD1C': "ultimajackpot_db",
        # 3xe dev
        # 3xe prod
    }
    return switcher.get(normalized_partner_id, "betz_db")
