from flask import Flask, render_template, request, jsonify
from models import ProductionOrder
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    orders = ProductionOrder.get_unplanned_orders()
    slots = ProductionOrder.get_schedule_slots()
    return render_template('index.html', orders=orders, schedule_slots=slots)


@app.route('/assign_order', methods=['POST'])
def assign_order():
    data = request.json
    order_no = data['order_no']
    plan_date = data['plan_date']
    shift = data['shift']

    order = next((o for o in ProductionOrder.get_unplanned_orders() if o['scgdh'] == order_no), None)
    if not order:
        return jsonify({'success': False, 'message': '工单不存在'})

    # 检查最早生产日期
    plan_date_obj = datetime.strptime(plan_date, '%Y-%m-%d').date()
    earliest_date = datetime.strptime(order['zzscrq'], '%Y-%m-%d').date()
    delivery_date = datetime.strptime(order['jhrq'], '%Y-%m-%d').date()


    # # 修改最早生产日期校验
    # if plan_date_obj < earliest_date:
    #     return jsonify({
    #         'success': 'warning',
    #         'message': f'警告：排产日期早于最早生产日期 {order["zzscrq"]}' 
    #     })
    
    # # 修改交货日期校验
    # if plan_date_obj > delivery_date:
    #     return jsonify({
    #         'success': 'warning',
    #         'message': f'警告：排产日期晚于交货日期 {order["jhrq"]}'
    #     })

    try:
        ProductionOrder.update_order_schedule(order_no, plan_date, shift)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/remove_order', methods=['POST'])
def remove_order():
    data = request.json
    order_no = data['order_no']

    try:
        ProductionOrder.reset_order_schedule(order_no)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/get_initial_data')
def get_initial_data():
    orders = ProductionOrder.get_unplanned_orders()
    slots = ProductionOrder.get_schedule_slots()
    return jsonify({
        'orders': orders,
        'slots': slots
    })

# 异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'系统异常: {str(e)}')
    return jsonify(success=False, message=f'系统错误: {str(e)}' if app.debug else '系统繁忙，请稍后重试'), 500


if __name__ == '__main__':
    app.run(debug=True)
