from flask import Blueprint, request, jsonify
from static.js.service.account_service import AccountService

# Blueprint 생성
account_bp = Blueprint('account', __name__, url_prefix='/api/account')

# 서비스 인스턴스 생성
account_service = AccountService()

@account_bp.route('/loadAccountList')
def read_account_list():
    accounts = account_service.get_all_accounts()
    return jsonify(accounts)

@account_bp.route('/createAccount', methods=['POST'])
def add_account():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    success, message = account_service.create_account(email, password)
    return jsonify({'success': success, 'message': message})

@account_bp.route('/deleteAccount', methods=['POST'])
def delete_account():
    data = request.get_json()
    email = data.get('email')

    success, message = account_service.delete_account(email)
    return jsonify({'success': success, 'message': message})
    
@account_bp.route('/updateAccount', methods=['POST'])
def update_account():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    success, message = account_service.update_account(email, password)
    return jsonify({'success': success, 'message': message})