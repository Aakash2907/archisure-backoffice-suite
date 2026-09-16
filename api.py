"""
REST API. One blueprint keeps the repo small; routes are grouped by the
business capability they implement (see README traceability table).
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from auth import login_required
from models import (Cost, Customer, CustomerBehavior, Payment, Policy,
                     Revenue, SmartDevice, db)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ---------- helpers ----------
def serialize_customer(c, detail=False):
    data = {
        'id': c.id, 'name': c.name, 'email': c.email, 'phone': c.phone,
        'satisfaction_score': c.satisfaction_score, 'retained': c.retained,
        'created_at': c.created_at.isoformat(),
    }
    if detail:
        data['devices'] = [{'id': d.id, 'type': d.device_type, 'status': d.status}
                            for d in c.devices]
        data['policies'] = [{'id': p.id, 'product': p.product, 'premium': p.premium,
                              'status': p.status} for p in c.policies]
        recent = sorted(c.behaviors, key=lambda x: x.timestamp, reverse=True)[:20]
        data['recent_behavior'] = [{'action': b.action, 'service': b.service,
                                     'timestamp': b.timestamp.isoformat()} for b in recent]
    return data


def serialize_policy(p):
    return {
        'id': p.id, 'customer_id': p.customer_id, 'customer_name': p.customer.name,
        'product': p.product, 'premium': p.premium, 'status': p.status,
        'created_at': p.created_at.isoformat(),
        'renewal_date': p.renewal_date.isoformat() if p.renewal_date else None,
    }


# ---------- Digital Customer Management ----------
@api_bp.route('/customers', methods=['GET'])
@login_required('admin', 'crm_manager', 'policy_officer', 'finance_manager')
def list_customers():
    q = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    query = Customer.query
    if q:
        query = query.filter(Customer.name.ilike(f'%{q}%'))
    pag = query.order_by(Customer.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'total': pag.total, 'page': page,
                     'customers': [serialize_customer(c) for c in pag.items]})


@api_bp.route('/customers', methods=['POST'])
@login_required('admin', 'crm_manager')
def create_customer():
    data = request.get_json(silent=True) or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({'error': 'name and email are required'}), 400
    c = Customer(name=data['name'], email=data['email'], phone=data.get('phone', ''))
    db.session.add(c)
    db.session.commit()
    return jsonify(serialize_customer(c)), 201


@api_bp.route('/customers/<int:cid>', methods=['GET'])
@login_required()
def get_customer(cid):
    if request.user['role'] == 'customer' and request.user.get('customer_id') != cid:
        return jsonify({'error': 'forbidden'}), 403
    c = Customer.query.get_or_404(cid)
    return jsonify(serialize_customer(c, detail=True))


@api_bp.route('/customers/summary', methods=['GET'])
@login_required('admin', 'crm_manager', 'finance_manager')
def customer_summary():
    total = Customer.query.count()
    active = Customer.query.filter_by(retained=True).count()
    avg_sat = db.session.query(db.func.avg(Customer.satisfaction_score)).scalar() or 0
    return jsonify({
        'total_customers': total, 'active_customers': active,
        'lost_customers': total - active,
        'satisfaction_score': round(avg_sat, 1),
    })


# ---------- CRM Data Access (shared service over the CRM data) ----------
@api_bp.route('/crm/customer/<int:cid>', methods=['GET'])
@login_required('admin', 'crm_manager', 'policy_officer', 'finance_manager')
def crm_customer_view(cid):
    c = Customer.query.get_or_404(cid)
    return jsonify(serialize_customer(c, detail=True))


# ---------- Smart Device Integration ----------
@api_bp.route('/devices', methods=['GET'])
@login_required('admin', 'crm_manager')
def list_devices():
    devices = SmartDevice.query.all()
    return jsonify([{'id': d.id, 'customer_id': d.customer_id, 'type': d.device_type,
                      'status': d.status, 'last_activity': d.last_activity.isoformat()}
                     for d in devices])


@api_bp.route('/devices', methods=['POST'])
@login_required('admin', 'crm_manager')
def add_device():
    data = request.get_json(silent=True) or {}
    if not data.get('customer_id'):
        return jsonify({'error': 'customer_id is required'}), 400
    d = SmartDevice(customer_id=data['customer_id'],
                     device_type=data.get('device_type', 'Smart Device'), status='active')
    db.session.add(d)
    db.session.commit()
    return jsonify({'id': d.id}), 201


@api_bp.route('/devices/<int:did>', methods=['DELETE'])
@login_required('admin', 'crm_manager')
def remove_device(did):
    d = SmartDevice.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    return jsonify({'deleted': did})


# ---------- Customer Behavior Analytics ----------
@api_bp.route('/behaviors', methods=['GET'])
@login_required('admin', 'crm_manager')
def list_behaviors():
    cid = request.args.get('customer_id')
    q = CustomerBehavior.query
    if cid:
        q = q.filter_by(customer_id=cid)
    rows = q.order_by(CustomerBehavior.timestamp.desc()).limit(200).all()
    return jsonify([{'id': b.id, 'customer_id': b.customer_id, 'action': b.action,
                      'service': b.service, 'timestamp': b.timestamp.isoformat()} for b in rows])


@api_bp.route('/behaviors', methods=['POST'])
@login_required()
def log_behavior():
    """Also implements 'Improve Customer Interaction with Collected Data':
    every logged action is available for personalization/insight downstream."""
    data = request.get_json(silent=True) or {}
    cid = data.get('customer_id') or request.user.get('customer_id')
    if not cid or not data.get('action'):
        return jsonify({'error': 'customer_id and action are required'}), 400
    b = CustomerBehavior(customer_id=cid, action=data['action'], service=data.get('service', ''))
    db.session.add(b)
    db.session.commit()
    return jsonify({'id': b.id}), 201


@api_bp.route('/analytics/behavior', methods=['GET'])
@login_required('admin', 'crm_manager', 'finance_manager')
def behavior_analytics():
    behaviors = CustomerBehavior.query.all()
    action_counts, service_counts = {}, {}
    for b in behaviors:
        action_counts[b.action] = action_counts.get(b.action, 0) + 1
        service_counts[b.service] = service_counts.get(b.service, 0) + 1
    at_risk = Customer.query.filter(Customer.satisfaction_score < 65).all()
    return jsonify({
        'action_counts': action_counts,
        'service_counts': service_counts,
        'at_risk_customers': [{'id': c.id, 'name': c.name,
                                'satisfaction_score': c.satisfaction_score} for c in at_risk],
    })


@api_bp.route('/analytics/recommendations/<int:cid>', methods=['GET'])
@login_required()
def recommendations(cid):
    """'Improve Customer Interaction with Collected Data': simple rule-based
    personalization derived from a customer's own behavior + device data."""
    if request.user['role'] == 'customer' and request.user.get('customer_id') != cid:
        return jsonify({'error': 'forbidden'}), 403
    c = Customer.query.get_or_404(cid)
    owned_products = {p.product for p in c.policies}
    used_services = {b.service for b in c.behaviors}
    suggestions = [p for p in ['Auto Insurance', 'Home Insurance', 'Life Insurance', 'Health Insurance']
                   if p not in owned_products and p in used_services]
    if not suggestions:
        suggestions = [p for p in ['Auto Insurance', 'Home Insurance', 'Life Insurance', 'Health Insurance']
                       if p not in owned_products][:2]
    notifications = []
    if c.satisfaction_score < 65:
        notifications.append('We would like to check in — a retention specialist can reach out.')
    if any(d.status == 'inactive' for d in c.devices):
        notifications.append('One of your smart devices looks inactive — reconnect it for better rates.')
    return jsonify({'customer_id': cid, 'recommended_products': suggestions,
                     'notifications': notifications})


# ---------- Policy Administration Services ----------
@api_bp.route('/policies', methods=['GET'])
@login_required('admin', 'policy_officer', 'crm_manager')
def list_policies():
    q = request.args.get('q', '')
    query = Policy.query
    if q:
        query = query.join(Customer).filter(Customer.name.ilike(f'%{q}%'))
    return jsonify([serialize_policy(p) for p in query.order_by(Policy.id.desc()).all()])


@api_bp.route('/policies', methods=['POST'])
@login_required('admin', 'policy_officer')
def create_policy():
    data = request.get_json(silent=True) or {}
    if not data.get('customer_id'):
        return jsonify({'error': 'customer_id is required'}), 400
    p = Policy(customer_id=data['customer_id'], product=data.get('product', 'Auto Insurance'),
               premium=float(data.get('premium', 0)), status='active',
               renewal_date=datetime.utcnow() + timedelta(days=365))
    db.session.add(p)
    db.session.commit()
    return jsonify(serialize_policy(p)), 201


@api_bp.route('/policies/<int:pid>', methods=['GET'])
@login_required()
def get_policy(pid):
    p = Policy.query.get_or_404(pid)
    if request.user['role'] == 'customer' and request.user.get('customer_id') != p.customer_id:
        return jsonify({'error': 'forbidden'}), 403
    return jsonify(serialize_policy(p))


@api_bp.route('/policies/<int:pid>', methods=['PUT'])
@login_required('admin', 'policy_officer')
def update_policy(pid):
    p = Policy.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    for field in ('product', 'premium', 'status'):
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify(serialize_policy(p))


@api_bp.route('/policies/<int:pid>/cancel', methods=['POST'])
@login_required('admin', 'policy_officer')
def cancel_policy(pid):
    p = Policy.query.get_or_404(pid)
    p.status = 'cancelled'
    db.session.commit()
    return jsonify(serialize_policy(p))


@api_bp.route('/policies/<int:pid>/renew', methods=['POST'])
@login_required('admin', 'policy_officer')
def renew_policy(pid):
    p = Policy.query.get_or_404(pid)
    p.status = 'active'
    p.renewal_date = datetime.utcnow() + timedelta(days=365)
    db.session.commit()
    return jsonify(serialize_policy(p))


# ---------- Financial Services (revenue, costs, payments, profitability) ----------
@api_bp.route('/payments', methods=['POST'])
@login_required('admin', 'finance_manager', 'policy_officer')
def add_payment():
    data = request.get_json(silent=True) or {}
    policy = Policy.query.get_or_404(data.get('policy_id'))
    amount = float(data.get('amount', policy.premium))
    pay = Payment(policy_id=policy.id, amount=amount)
    db.session.add(pay)
    db.session.add(Revenue(source='premium', customer_id=policy.customer_id, amount=amount))
    db.session.commit()
    return jsonify({'id': pay.id}), 201


@api_bp.route('/revenue', methods=['GET'])
@login_required('admin', 'finance_manager')
def list_revenue():
    rows = Revenue.query.order_by(Revenue.date.desc()).limit(200).all()
    return jsonify([{'id': r.id, 'source': r.source, 'customer_id': r.customer_id,
                      'amount': r.amount, 'date': r.date.isoformat()} for r in rows])


@api_bp.route('/revenue', methods=['POST'])
@login_required('admin', 'finance_manager')
def add_revenue():
    data = request.get_json(silent=True) or {}
    r = Revenue(source=data.get('source', 'manual'), customer_id=data.get('customer_id'),
                amount=float(data['amount']))
    db.session.add(r)
    db.session.commit()
    return jsonify({'id': r.id}), 201


@api_bp.route('/costs', methods=['GET'])
@login_required('admin', 'finance_manager')
def list_costs():
    rows = Cost.query.order_by(Cost.date.desc()).limit(200).all()
    return jsonify([{'id': c.id, 'type': c.type, 'amount': c.amount,
                      'date': c.date.isoformat()} for c in rows])


@api_bp.route('/costs', methods=['POST'])
@login_required('admin', 'finance_manager')
def add_cost():
    data = request.get_json(silent=True) or {}
    c = Cost(type=data.get('type', 'other'), amount=float(data['amount']))
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id}), 201


@api_bp.route('/financial/summary', methods=['GET'])
@login_required('admin', 'finance_manager', 'crm_manager')
def financial_summary():
    total_revenue = db.session.query(db.func.sum(Revenue.amount)).scalar() or 0
    total_cost = db.session.query(db.func.sum(Cost.amount)).scalar() or 0
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue else 0
    personnel = db.session.query(db.func.sum(Cost.amount)).filter_by(type='personnel').scalar() or 0
    maintenance = db.session.query(db.func.sum(Cost.amount)).filter_by(type='maintenance').scalar() or 0
    return jsonify({
        'total_revenue': round(total_revenue, 2), 'total_cost': round(total_cost, 2),
        'net_profit': round(profit, 2), 'profit_margin': round(margin, 2),
        'personnel_cost': round(personnel, 2), 'maintenance_cost': round(maintenance, 2),
    })


# ---------- Data Driven Insurance ----------
@api_bp.route('/insurance/risk/<int:cid>', methods=['GET'])
@login_required('admin', 'crm_manager', 'policy_officer')
def risk_score(cid):
    """Transparent rule-based demo score — NOT real underwriting."""
    c = Customer.query.get_or_404(cid)
    score = 50.0
    score -= sum(1 for d in c.devices if d.status == 'active') * 5
    score -= (c.satisfaction_score - 70) * 0.3
    score += sum(1 for b in c.behaviors if b.action == 'file_claim') * 10
    score = max(5, min(95, round(score, 1)))
    base_premium = 150
    recommended_premium = round(base_premium * (1 + (score - 50) / 100), 2)
    return jsonify({
        'customer_id': cid, 'risk_score': score, 'recommended_premium': recommended_premium,
        'factors': {
            'active_devices': sum(1 for d in c.devices if d.status == 'active'),
            'satisfaction_score': c.satisfaction_score,
            'claims_filed': sum(1 for b in c.behaviors if b.action == 'file_claim'),
        },
        'note': 'Demonstration rule-based score only — not real insurance underwriting.',
    })


# ---------- Main Dashboard / KPIs ----------
@api_bp.route('/dashboard', methods=['GET'])
@login_required()
def dashboard():
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(retained=True).count()
    avg_satisfaction = db.session.query(db.func.avg(Customer.satisfaction_score)).scalar() or 0
    total_revenue = db.session.query(db.func.sum(Revenue.amount)).scalar() or 0
    total_cost = db.session.query(db.func.sum(Cost.amount)).scalar() or 0
    active_policies = Policy.query.filter_by(status='active').count()
    retention_rate = round(active_customers / total_customers * 100, 1) if total_customers else 0
    market_share = round(min(35, 10 + active_policies * 0.2), 1)  # simulated KPI
    return jsonify({
        'sales_target': 500000,
        'revenue': round(total_revenue, 2), 'costs': round(total_cost, 2),
        'profit': round(total_revenue - total_cost, 2),
        'customer_satisfaction': round(avg_satisfaction, 1),
        'total_customers': total_customers, 'active_customers': active_customers,
        'lost_customers': total_customers - active_customers,
        'retention_rate': retention_rate, 'market_share': market_share,
        'active_policies': active_policies,
    })


@api_bp.route('/dashboard/trends', methods=['GET'])
@login_required()
def dashboard_trends():
    months, now = [], datetime.utcnow()
    for i in range(5, -1, -1):
        start, end = now - timedelta(days=30 * (i + 1)), now - timedelta(days=30 * i)
        rev = db.session.query(db.func.sum(Revenue.amount)).filter(
            Revenue.date >= start, Revenue.date < end).scalar() or 0
        cost = db.session.query(db.func.sum(Cost.amount)).filter(
            Cost.date >= start, Cost.date < end).scalar() or 0
        months.append({'label': start.strftime('%b'), 'revenue': round(rev, 2),
                        'cost': round(cost, 2), 'profit': round(rev - cost, 2)})
    return jsonify(months)
