from flask import Flask, render_template, request, jsonify
from models import ProductionOrderService
from datetime import datetime, timedelta
import os

from flask import Flask, jsonify

app = Flask(__name__)
# 添加JSON中文支持配置
app.config['JSON_AS_ASCII'] = False  # 关键配置：禁用ASCII编码
app.config['JSON_SORT_KEYS'] = False  # 可选：保持JSON键顺序与字典一致


@app.route('/')
def new_index():
    return render_template('index.html')

#排产页
@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')

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
        start_time=data['start_time'],
        jhwgrq=data['jhwgrq'],
        jhwgsj=data['jhwgsj']
    )
    return jsonify(result)

# 取消排产接口
@app.route('/api/unschedule', methods=['POST'])
def unschedule_order():
    order_no = request.json.get('order_no')
    result = ProductionOrderService().unschedule_order(order_no)
    return jsonify(result)

#查询页
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

@app.route('/upload')
def upload():
    return render_template('upload.html')  # 需要创建对应的模板

# 工单详情页
@app.route('/order')
def order_detail():
    order_no = request.args.get('no')
    if not order_no:
        return "Order number is required", 400
    print(order_no)
    details = ProductionOrderService().get_order_details(order_no)
    return render_template('order_detail.html', order=details)

@app.route('/api/order/<order_no>')
def order_data(order_no):
    try:
        details = ProductionOrderService().get_order_details(order_no)
        if details:
            return jsonify(details)  # 现在中文会正常显示
        return jsonify({"error": "订单不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# 预约工单页面
@app.route('/appointment_order')
def appointment_order_page():
    return render_template('appointment_order.html')

# 获取预约工单数据
@app.route('/api/appointment_orders')
def get_appointment_orders():
    # 获取查询参数
    khmc = request.args.get('khmc')
    ywy = request.args.get('ywy')
    jhrq = request.args.get('jhrq')
    yygdh = request.args.get('yygdh')
    
    service = ProductionOrderService()
    orders = service.get_appointment_orders(khmc, ywy, jhrq, yygdh)
    return jsonify(orders)

# 添加预约工单
@app.route('/api/appointment_orders', methods=['POST'])
def add_appointment_order():
    data = request.json
    service = ProductionOrderService()
    result = service.add_appointment_order(data)
    return jsonify(result)

# 更新预约工单
@app.route('/api/appointment_orders/<yygdh>', methods=['PUT'])
def update_appointment_order(yygdh):
    data = request.json
    service = ProductionOrderService()
    result = service.update_appointment_order(yygdh, data)
    return jsonify(result)

# 删除预约工单
@app.route('/api/appointment_orders/delete', methods=['POST'])
def delete_appointment_orders():
    data = request.json
    ids = data.get('ids', [])
    service = ProductionOrderService()
    result = service.delete_appointment_orders(ids)
    return jsonify(result)

# 获取单个预约工单详情 暂时无详情页
@app.route('/api/appointment_orders/<yygdh>')
def get_appointment_order_detail(yygdh):
    service = ProductionOrderService()
    order = service.get_appointment_order_detail(yygdh)
    return jsonify(order)

if __name__ == '__main__':
    app.run(debug=True,port=5003)
