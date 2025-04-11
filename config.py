import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据文件路径
DATA_FILES = {
    'factory_data': os.path.join(BASE_DIR, '苏州、天津工厂数据总览.csv'),
    'supplier_data': os.path.join(BASE_DIR, '供应商2024-2025采购数据汇总.csv'),
    'category_data': os.path.join(BASE_DIR, '各Subcategory-Spend汇总.csv')
}

# 文件编码设置
FILE_ENCODING = 'utf-8' 