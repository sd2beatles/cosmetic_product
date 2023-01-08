import pandas as pd
import numpy as np
import re

def label_change(country):
    if country=="china":
        return 'China'
    elif country=="vn":
        return  "Vietnam"
    elif country=="Arabia":
        return "Saudi"
    elif country in ['america','America']:
        return "U.S.A"
    else:
        return country
    
def crawler_check(url):
    crawlers=['boto','spider','googlebot','baidspider','yeti','yahoo','tumbir','mj12bot',
              'yadex','bot','semrushbot','adsbot','facebot','robots']
    for cralwer in crawlers:
        if url.lower() in cralwer:
            return True
    return False

def price_preprocess(df):
    def convert_price(price):
        return float(re.search("\$([0-9]{,4}.[0-9]{,2})",price.replace(",","")).group(1))
        
    df.original_price=df.original_price.map(lambda x:convert_price(x))
    df.speical_price=df.speical_price.map(lambda x:convert_price(x))
    
    abnormal=df[df.speical_price/df.original_price<0.1].index
    df.loc[abnormal,'original_price']=df.loc[abnormal,'original_price']/100
    return df
    

 

