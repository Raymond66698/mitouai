"""Test Qlib fetch_from_tushare_db"""
import sys, os, time
sys.path.insert(0, '/opt/mitouai/backend')
os.environ.setdefault('DATABASE_URL', 'postgresql://mitouai:Mitouai%402026%21@127.0.0.1:5432/mitouai')

from services.qlib_integration.data_pipeline import QlibDataPipeline

pipeline = QlibDataPipeline(qlib_data_dir='/opt/mitouai/backend/qlib_data')

# Test 1: 单只股票读取
print('=== Test 1: 单只股票从DB读取 ===')
start = time.time()
df = pipeline.fetch_from_tushare_db('000001', start_date='20260101', end_date='20260723')
elapsed = time.time() - start
print(f'000001: {len(df)} rows, {elapsed:.3f}s')
if not df.empty:
    print(df.head(3).to_string())
    print(f'columns: {list(df.columns)}')

# Test 2: 批量读取10只
print('\n=== Test 2: 批量10只 ===')
codes = ['000001','000002','000858','600519','601318','000333','002475','300750','600036','601398']
start = time.time()
results = pipeline.fetch_multi_from_tushare_db(codes, start_date='20260101', end_date='20260723')
elapsed = time.time() - start
print(f'10 stocks: {len(results)} ok, {elapsed:.2f}s (avg {elapsed/10:.3f}s/stock)')

# Test 3: 刷新 .bin
print('\n=== Test 3: 刷新Qlib .bin ===')
start = time.time()
r = pipeline.refresh_from_tushare_db(codes, days_back=1095)
elapsed = time.time() - start
print(f'Result: {r}')
print(f'Elapsed: {elapsed:.1f}s')

# Test 4: 状态
status = pipeline.get_status()
print(f'\n=== Qlib Status ===')
print(f'Calendar days: {status["calendar_days"]}')
print(f'Stocks: {status["stock_count"]}')
print(f'Bin files: {status["bin_files"]}')
print(f'Size: {status["total_size_mb"]}MB')
