from flask import Flask, render_template, request, jsonify
from models import ProductionOrderService
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 获取待排产工单
@app.route('/api/orders')
def get_orders():
    service = ProductionOrderService()
    orders = service.get_pending_orders()
    return jsonify(orders)

# 获取已排产工单
@app.route('/api/scheduled_orders')
def get_scheduled_orders():
    service = ProductionOrderService()
    orders = service.get_scheduled_orders()
    return jsonify(orders)

# 排产操作接口
@app.route('/api/schedule', methods=['POST'])
def schedule_order():
    data = request.json
    result = ProductionOrderService().schedule_order(
        order_no=data['order_no'],
        plan_date=data['plan_date'],
        shift=data['shift'],
        start_time=data['start_time']
    )
    return jsonify(result)

# 取消排产接口
@app.route('/api/unschedule', methods=['POST'])
def unschedule_order():
    order_no = request.json.get('order_no')
    result = ProductionOrderService().unschedule_order(order_no)
    return jsonify(result)

@app.route('/query')
def query_page():
    return render_template('query.html')

# 添加API路由用于获取所有工单数据
@app.route('/api/all_orders')
def get_all_orders():
    service = ProductionOrderService()
    orders = service.get_all_orders()
    return jsonify(orders)

# 添加API路由用于保存编辑后的数据
@app.route('/api/update_order', methods=['POST'])
def update_order():
    data = request.json
    result = ProductionOrderService().update_order(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
