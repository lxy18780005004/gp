from flask import Flask, jsonify
from flask_cors import CORS
import tushare as ts
import config
import redis
import json
import hashlib

app = Flask(__name__)
CORS(app)

# 初始化 Tushare
ts.set_token(config.TUSHARE_TOKEN)
pro = ts.pro_api()

# 初始化 Redis
try:
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=config.REDIS_DECODE_RESPONSES
    )
    redis_client.ping()
    print("Redis 连接成功")
except Exception as e:
    print(f"Redis 连接失败: {e}")
    redis_client = None

def get_cache_key(prefix, **kwargs):
    """生成缓存键"""
    key_str = f"{prefix}:" + ":".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return hashlib.md5(key_str.encode()).hexdigest()

def get_from_cache(key):
    """从缓存获取数据"""
    if not redis_client:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"缓存读取失败: {e}")
    return None

def set_to_cache(key, data, expire=None):
    """设置缓存"""
    if not redis_client:
        return False
    try:
        redis_client.setex(
            key,
            expire or config.CACHE_EXPIRE_TIME,
            json.dumps(data, ensure_ascii=False)
        )
        return True
    except Exception as e:
        print(f"缓存写入失败: {e}")
    return False

@app.route('/api/health', methods=['GET'])
def health():
    redis_status = 'connected' if redis_client else 'disconnected'
    try:
        if redis_client:
            redis_client.ping()
            redis_status = 'connected'
    except:
        redis_status = 'disconnected'
    
    return jsonify({
        'status': 'ok', 
        'message': 'Backend is running',
        'redis': redis_status
    })

@app.route('/api/stock/list', methods=['GET'])
def get_stock_list():
    try:
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market')
        data = df.head(20).to_dict('records')
        return jsonify({'code': 0, 'data': data})
    except Exception as e:
        return jsonify({'code': -1, 'message': str(e)}), 500

@app.route('/api/stock/kline', methods=['GET'])
def get_kline():
    from flask import request
    
    ts_code = request.args.get('ts_code')
    freq = request.args.get('freq', 'D')  # D=日, W=周, M=月
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    if not ts_code:
        return jsonify({'code': -1, 'message': '股票代码不能为空'}), 400
    
    # 生成缓存键
    cache_key = get_cache_key('kline', ts_code=ts_code, freq=freq, start=start_date, end=end_date)
    
    # 尝试从缓存获取
    cached_data = get_from_cache(cache_key)
    if cached_data:
        print(f"从缓存获取数据: {ts_code}")
        return jsonify(cached_data)
    
    try:
        # 获取股票基本信息
        stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,area,industry')
        stock_name = stock_info.iloc[0]['name'] if not stock_info.empty else ts_code
        
        # 根据周期获取不同的K线数据
        if freq == 'W':
            print(f"调用周线接口: {ts_code}")
            df = pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')
        elif freq == 'M':
            print(f"调用月线接口: {ts_code}")
            df = pro.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')
        else:  # D
            print(f"调用日线接口: {ts_code}")
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')
        
        print(f"获取到 {len(df)} 条数据，周期: {freq}")
        
        if df.empty:
            result = {'code': 0, 'data': [], 'name': stock_name, 'info': {}, 'freq': freq}
            return jsonify(result)
        
        # 按日期排序
        df = df.sort_values('trade_date')
        
        # 获取最新数据的涨跌幅等指标（直接使用Tushare返回的数据）
        latest = df.iloc[-1]
        
        info = {
            'latest_price': float(latest['close']),
            'change': float(latest['change']) if 'change' in latest and latest['change'] else 0,
            'change_pct': float(latest['pct_chg']) if 'pct_chg' in latest and latest['pct_chg'] else 0,
            'high': float(latest['high']),
            'low': float(latest['low']),
            'volume': float(latest['vol']),
            'date': latest['trade_date']
        }
        
        # 转换为前端需要的格式
        data = []
        for idx, row in df.iterrows():
            # 使用Tushare返回的涨跌幅数据
            open_price = float(row['open'])
            close_price = float(row['close'])
            
            # 直接使用Tushare的涨跌额和涨跌幅
            change_amount = float(row['change']) if 'change' in row and row['change'] else (close_price - open_price)
            change_percent = float(row['pct_chg']) if 'pct_chg' in row and row['pct_chg'] else 0
            
            # 计算资金流入流出（成交额 * 涨跌幅作为简化指标）
            amount = float(row['amount']) if 'amount' in row else 0
            money_flow = amount * (change_percent / 100) if amount > 0 else 0
            
            data.append({
                'date': row['trade_date'],
                'open': open_price,
                'close': close_price,
                'high': float(row['high']),
                'low': float(row['low']),
                'vol': float(row['vol']),
                'amount': amount,
                'change': round(change_amount, 2),
                'change_pct': round(change_percent, 2),
                'money_flow': round(money_flow, 2)
            })
        
        result = {'code': 0, 'data': data, 'name': stock_name, 'info': info, 'freq': freq}
        
        # 存入缓存
        set_to_cache(cache_key, result)
        print(f"数据已缓存: {ts_code} ({freq})")
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'code': -1, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
