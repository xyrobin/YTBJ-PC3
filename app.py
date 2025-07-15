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

#工单查询列表页
@app.route('/query')
def query_page():
    return render_template('query.html')

# 添加API路由用于获取所有工单数据
@app.route('/api/all_orders')
def get_all_orders():
    # 获取查询参数
    scgdh = request.args.get('scgdh')
    gdjhzt = request.args.get('gdjhzt')
    jhrq = request.args.get('jhrq')
    ywy = request.args.get('ywy')
    jhksrq = request.args.get('jhksrq')
    khmc = request.args.get('khmc')
    gg = request.args.get('gg')
    
    service = ProductionOrderService()
    orders = service.get_all_orders(
        scgdh=scgdh, 
        gdjhzt=gdjhzt, 
        jhrq=jhrq, 
        ywy=ywy, 
        jhksrq=jhksrq, 
        khmc=khmc, 
        gg=gg
    )
    return jsonify(orders)

# 更新工单API
@app.route('/api/update_order', methods=['POST'])
def update_order():
    data = request.json
    result = ProductionOrderService().update_order(data)
    return jsonify(result)

# 更新工单-工时API
@app.route('/api/update_order_gs', methods=['POST'])
def update_order_gs():
    data = request.json
    result = ProductionOrderService().update_order_gs(data)
    return jsonify(result)

# 占位
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

# 获取工单详情API
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

# 获取预约工单数据API
@app.route('/api/appointment_orders')
def get_appointment_orders():
    # 获取查询参数
    khmc = request.args.get('khmc')
    ywy = request.args.get('ywy')
    jhrq = request.args.get('jhrq')
    yygdh = request.args.get('yygdh')
    scgdh = request.args.get('scgdh')
    is_deleted = request.args.get('is_deleted')
    gdjhzt = request.args.get('gdjhzt')
    
    service = ProductionOrderService()
    orders = service.get_appointment_orders(khmc, ywy, jhrq, yygdh,scgdh,is_deleted,gdjhzt)
    return jsonify(orders)

# 添加预约工单API
@app.route('/api/appointment_orders', methods=['POST'])
def add_appointment_order():
    data = request.json
    service = ProductionOrderService()
    result = service.add_appointment_order(data)
    return jsonify(result)

# 更新预约工单API
@app.route('/api/appointment_orders/<yygdh>', methods=['PUT'])
def update_appointment_order(yygdh):
    data = request.json
    service = ProductionOrderService()
    result = service.update_appointment_order(yygdh, data)
    return jsonify(result)

# 删除预约工单API
@app.route('/api/appointment_orders/delete', methods=['POST'])
def delete_appointment_orders():
    data = request.json
    ids = data.get('ids', [])
    service = ProductionOrderService()
    result = service.delete_appointment_orders(ids)
    return jsonify(result)

#单个预约工单详情页
@app.route('/appointment_order_detail')
def appointment_order_detail():
    yygdh = request.args.get('yygdh')
    if not yygdh:
        return "Order number is required", 400
    print(yygdh)
    details = ProductionOrderService().get_appointment_order_detail(yygdh)
    return render_template('appointment_order_detail.html', order=details)


# 获取单个预约工单详情API
@app.route('/api/appointment_orders/<yygdh>')
def get_appointment_order_detail(yygdh):
    service = ProductionOrderService()
    order = service.get_appointment_order_detail(yygdh)
    return jsonify(order)

#预约工单绑定生产工单API
@app.route('/api/appointment_orders/<yygdh>/bind', methods=['POST'])
def bind_appointment_order(yygdh):
    try:
        data = request.get_json()
        scgdh = data.get('scgdh')
        if not scgdh:
            return jsonify({'success': False, 'message': '生产工单号不能为空'})

        # 调用模型层方法更新生产工单号
        result = ProductionOrderService().bind_appointment_order(yygdh, scgdh)
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '更新失败，请检查工单号是否存在且已同步，工单不能为已排产或已被绑定状态'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 预约工单取消API
@app.route('/api/appointment_orders/<yygdh>/cancel', methods=['POST'])
def cancel_appointment_order(yygdh):
    try:
        # 调用模型层方法取消预约工单
        result = ProductionOrderService().cancel_appointment_order(yygdh)
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '取消失败，请检查工单状态是否为待排产且未被绑定'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 尝试打开报表页面
@app.route('/inventory_report')
def inventory_report():
    return render_template('inventory_report.html')
        
if __name__ == '__main__':
    app.run(debug=True,port=5003)

