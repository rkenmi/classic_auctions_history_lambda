import json
import boto3
from datetime import datetime
import os
from collections import deque, Counter, defaultdict
import psycopg2
from psycopg2.extras import execute_values

s3 = boto3.client('s3')
BUCKET = os.environ['S3_BUCKET']
RDBMS_HOST = os.environ['RDBMS_HOST']
RDBMS_PW = os.environ['RDBMS_PW']
RDBMS_USER = os.environ['RDBMS_USER']

def lambda_handler(event, context):
    pg = psycopg2.connect("host={0} user={1} password={2} dbname=postgres".format(RDBMS_HOST, RDBMS_USER, RDBMS_PW))
    realms = ['oldblanchy', 'anathema', 'arcanitereaper', 'atiesh', 'azuresong',
              'bigglesworth', 'blaumeux', 'fairbanks', 'grobbulus', 'kurinnaxx', 'myzrael',
              'rattlegore', 'smolderweb', 'thunderfury', 'whitemane']

    factions = ['horde', 'alliance']

    for realm in realms:
        for faction in factions:
            response = s3.get_object(Bucket=BUCKET, Key="realm/{0}/{1}/items.json".format(realm, faction))
            json_body = response['Body'].read()
            items = json.loads(json.loads(json_body))

            price_map = defaultdict(Counter)

            for item in items:
                price_map[item['id']]['qty'] += int(item['quantity'])

                if price_map[item['id']]['price'] == 0:
                    price_map[item['id']]['price'] = int(item['buyout'])
                else:
                    price_map[item['id']]['price'] = min(
                        int(item['buyout']),
                        price_map[item['id']]['price']
                    )

            cursor = pg.cursor()

            rows = []
            for id, data in price_map.items():
                rows.append( (realm, faction, id, data['price'], data['qty'], str(datetime.now())) )

            execute_values(cursor, "INSERT INTO ah_marketprice (realm, faction, item_id, price, quantity, timestamp) VALUES %s", rows)

            cursor.close()
            pg.commit()

    pg.close()


    return response['ContentType']
