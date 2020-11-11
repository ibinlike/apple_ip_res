# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import numpy as np
import sched, time
import sys
import webbrowser


# Links:
ip12p_ava = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/A/availability.json'
ip12_ava = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/F/availability.json'
ip12mini_ava = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/H/availability.json'
ip12pm_ava = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/G/availability.json'
ip12_res = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/F/availability?iUP=N'
ip12p_res = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/A/availability?iUP=N'
ip12mini_res = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/H/availability?iUP=N'
ip12pm_res = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/G/availability?iUP=N'
store_data = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/A/stores.json'
time_stamp = ''

# get the model description
def get_model_mapping(model_name):
    url = ''
    if model_name == 'Iphone12 Pro':
      url = ip12p_res
    elif model_name =='Iphone12':
      url = ip12_res
    elif model_name == 'Iphone12 Mini':
      url = ip12mini_res
    elif model_name == 'Iphone12 Pro Max':
      url = ip12pm_res
    r = requests.get(url)
    bs = BeautifulSoup(r.content, features="html.parser")
    model_name = []
    model_desc = []
    for i in bs.find_all('script'):
      if 'data.products' in str(i):
        for line in str(i).splitlines()[30:]:
          if "partNumber" in line:     
            name = line.split(':')[1].replace("\\", '')
            name = name.replace(',', '')
            name = name.replace('"', '').strip()   
            model_name.append(name)
          elif "description" in line:
            desc = line.split(':')[1].strip()
            desc = desc.replace(',', '')
            desc = desc.replace('"', '').strip() 
            model_desc.append(desc)             
    model_map = {model_name[i]:model_desc[i] for i in range(len(model_name))}
    return model_map

#get store 
def get_store_mapping(urls):
    r = requests.get(urls)
    bs = BeautifulSoup(r.content, features="html.parser")
    store_mapping = {}
    for store in json.loads(bs.text)['stores']:
        if (store['enabled']):
            store_mapping[store['storeNumber']] = [store['city'], store['storeName']]
    return store_mapping

# convert the dict to bool
def convert_dic(dict_b):
    if dict_b['availability']['unlocked'] == False:
        return None
    else:
        return True


# get the status json file and process it to df
def process_apple_data(urls):
    availability = requests.get(urls)
    availability_content = json.loads(availability.text)
    df = pd.DataFrame.from_dict(availability_content)
    df = df[['updated', 'stores']]
    global time_stamp
    if df['updated'][0] == time_stamp:
        exit()
    else:
        time_stamp = df['updated'][0]
        df.drop('zh_CN', inplace = True)
        new_df = pd.concat([df.drop(['stores'], axis = 1), df['stores'].apply(pd.Series)], axis = 1).reset_index()
        new_df.rename(columns = {'index':'stores'}, inplace = True)
        new_df.iloc[:, 2:] = new_df.iloc[:, 2:].applymap(convert_dic)
        new_df.drop('updated', axis = 1, inplace = True)
        new_df = new_df[new_df[new_df.columns[1:]].sum(axis = 1) > 0 ].reset_index()
        return new_df

# Based on the stock avaiability, return the store name and model name:
def extract_info(df, store_mapping, model_mapping, store_to_monitor, model_exact_name, m):
    link_1 = 'https://reserve-prime.apple.com/CN/zh_CN/reserve/'
    link_2 = '?color='
    link_3 = '&capacity='
    link_4 = '&quantity=1&anchor-store='
    link_5 = '&store='
    link_6 = '&partNumber='
    link_7 = '&channel=&sourceID=&iUID=&iuToken=&iUP=N&appleCare=&rv=&path=&plan=unlocked'
    store_inter_sect = list(set(store_to_monitor) & set(df.stores.tolist()))
    if store_inter_sect:
        for s in store_inter_sect:
            store_c_n = store_mapping[s]
            store_city, store_name = store_c_n[0], store_c_n[1] 
            final_df = df.loc[df['stores'] == s].dropna(axis = 1)
            col_list = final_df.columns.tolist()
            model_list = col_list[2:]
            inter_sect = list(set(model_list) & set(model_exact_name))
            if inter_sect:
                for e in inter_sect:
                    modelName = model_mapping[e]
                    col = modelName[-3:].strip()
                    capacity = modelName[-9:-4].strip()
                    print(time_stamp, store_city, store_name, modelName)
                    final_link = ''.join([link_1,m,link_2,col,link_3,capacity,link_4,s,link_5,s,link_6,e,link_7])
                    print(final_link)
                    webbrowser.open(final_link)
            else:
                pass
    else:
        pass
      
# Monitor the stock
def monitor_res(urls, store_mapping, model_mapping, store_to_monitor, model_exact_name, m, model_name):
    try:
        df = process_apple_data(urls)
        if len(df) > 0:
            extract_info(df, store_mapping, model_mapping, store_to_monitor, model_exact_name, m)
        else:
            print(time_stamp, model_name, '监测中...')
    except:
        pass

# return ava link and m

def return_ava_m(model_name):

    if model_name == 'Iphone12':
        ava_link = ip12_ava
        m = 'F'
    elif model_name == 'Iphone12 Pro':
        ava_link = ip12p_ava
        m = 'A'
    elif model_name == 'Iphone12 Mini':
        ava_link = ip12mini_ava
        m = 'H'
    elif model_name == 'Iphone12 Pro Max':
        ava_link = ip12pm_ava
        m = 'G'
    return ava_link, m


# print dic items

def print_dict(dicts):
    return   [print(k,':', v) for k, v in enumerate(list(dicts.items()))]

# validate the input
def vali_input(dicts):
    val = True
    while val == True:
        re_list =[]
        num = input('请输入需要监视的编号， 如果是多个请用英文输入法下的逗号隔开：')
        if num == '':
            re_list = dicts.keys()
            val = False
        else:
            if all(int(t) >= 0 and int(t) <= len(dicts) for t in num.split(',')):
                re_list =[]
                for t in num.split(','):
                    re_list.append(list(dicts.items())[int(t)][0])
                val = False
            else:
                print('请输入正确的序列号')
                continue
    return re_list

# return the model name

def input_model_name():
    val = True
    model_list = ['Iphone12 Mini', 'Iphone12','Iphone12 Pro', 'Iphone12 Pro Max']
    while val == True:
        [print(k, ":",  v) for k, v in enumerate(model_list)]
        num = input('请输入需要的型号编号（0-3）：')
        if (int(num) >= 0) and (int(num) <= len(model_list)):
            model_name = model_list[int(num)]
            val = False
        else:
            print('请输入正确的序列号')
            continue
    return model_name

 

def daemon(local_handler, t, store_mapping, model_mapping, ava_link,store_to_monitor, model_exact_name, m, model_name): 
  try:
      monitor_res(ava_link, store_mapping, model_mapping, store_to_monitor, model_exact_name, m, model_name)
      time.sleep(5)
      local_handler.enterabs(t + 5, 1, daemon, (local_handler, t+5, store_mapping, model_mapping, ava_link, store_to_monitor, model_exact_name, m, model_name))
  except:

      print('出错了， 休息10分钟继续！')
      time.sleep(600)
      print('再次监测')
      local_handler.enterabs(t + 5, 1, daemon, (local_handler, t+5, store_mapping, model_mapping, ava_link, store_to_monitor, model_exact_name, m, model_name))

def main():
    model_name = input_model_name()
    ava_link, m = return_ava_m(model_name)
    store_mapping = get_store_mapping(store_data)
    print_dict(store_mapping)
    store_to_monitor = vali_input(store_mapping)
    model_mapping = get_model_mapping(model_name)
    print_dict(model_mapping)
    model_exact_name = vali_input(model_mapping)
    print('监视的零售店：', [store_mapping[x] for x in store_to_monitor])
    print('监视的型号：', [model_mapping[x] for x in model_exact_name])
    handler = sched.scheduler(time.time, time.sleep)
    t = time.time()
    handler.enter(0, 1, daemon, (handler, t, store_mapping, model_mapping, ava_link, store_to_monitor, model_exact_name,m, model_name))
    handler.run()


if __name__ == "__main__":
    main()


