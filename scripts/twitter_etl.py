import tweepy
import pandas as pd
import json
import os
from datetime import datetime
import s3fs
import logging
from config import load_config
from xquik_export import load_xquik_export_rows

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
config = load_config()

def run_twitter_etl():
    try:
        s3_bucket = config['aws']['s3_bucket']
        s3_path = config['aws']['s3_path']
        xquik_export_path = os.getenv("XQUIK_EXPORT_PATH") or config.get("xquik", {}).get("export_path")

        if xquik_export_path:
            logging.info("Cargando exportación de Xquik")
            tweet_list = load_xquik_export_rows(xquik_export_path)
        else:
            bearer_token = config['twitter']['bearer_token']
            logging.info("Autenticación con Twitter")
            client = tweepy.Client(bearer_token=bearer_token)

            username = "elonmusk"
            user = client.get_user(username=username)
            user_id = user.data.id

            tweets = client.get_users_tweets(user_id, max_results=100, tweet_fields=['created_at', 'public_metrics', 'text'], exclude='retweets')

            tweet_list = []
            logging.info("Extracción de tweets")
            for tweet in tweets.data:
                refined_tweet = {
                    "user": username,
                    'text': tweet.text,
                    'favorite_count': tweet.public_metrics['like_count'],
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'created_at': tweet.created_at
                }
                tweet_list.append(refined_tweet)

        df = pd.DataFrame(tweet_list)
        logging.info("Transformación de tweets a DataFrame")
        df.to_csv('refined_tweets.csv')
        logging.info("Guardando archivo CSV")

        # Cargar a S3
        df.to_csv(f's3://{s3_bucket}/{s3_path}/refined_tweets.csv')
        logging.info("Archivo subido a S3")

    except tweepy.errors.Forbidden as e:
        logging.error("Error de autenticación: Verifica tus credenciales y permisos.")
        logging.error(e)
    except Exception as e:
        logging.error("Ocurrió un error.")
        logging.error(e)
