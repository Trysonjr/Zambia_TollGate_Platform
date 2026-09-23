import unittest
import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database import db
from models import User, TollAccount, Vehicle, Tollgate, Transaction, Payment, AuditLog
from services.toll_service import (
    calculate_toll_fee, lookup_vehicle, lookup_by_rfid, 
    process_toll_payment, normalize_plate
)
from init_db import seed_database

class TestZambiaTollgatePlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(force_sqlite=True)
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            seed_database()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_tariff_calculation(self):
        """Test statutory Zambian toll fee calculation."""
        self.assertEqual(calculate_toll_fee('Light Vehicle'), 20.00)
        self.assertEqual(calculate_toll_fee('Medium Vehicle'), 50.00)
        self.assertEqual(calculate_toll_fee('Heavy Vehicle'), 100.00)
        self.assertEqual(calculate_toll_fee('Abnormal Load'), 250.00)

    def test_02_plate_normalization(self):
        """Test license plate normalization and space handling."""
        self.assertEqual(normalize_plate('abc 1234'), 'ABC 1234')
        self.assertEqual(normalize_plate('  blz   8899  '), 'BLZ 8899')

    def test_03_vehicle_lookup(self):
        """Test vehicle, owner, and toll account retrieval."""
        res = lookup_vehicle('ABC 1234')
        self.assertIsNotNone(res)
        self.assertEqual(res['vehicle'].registration_number, 'ABC 1234')
        self.assertEqual(res['vehicle'].rfid_tag, 'TAG-001')
        self.assertEqual(res['owner'].email, 'motorist@test.zm')
        self.assertGreaterEqual(res['balance'], 20.00)

    def test_04_successful_toll_deduction_and_barrier(self):
        """Test core flow: ABC 1234 deduction of K20 and barrier trigger."""
        account = TollAccount.query.join(User).filter(User.email == 'motorist@test.zm').first()
        initial_balance = float(account.balance)
        
        tollgate = Tollgate.query.filter_by(name='Lusaka East Toll Plaza').first()
        result = process_toll_payment(
            vehicle_reg='ABC 1234',
            vehicle_type='Light Vehicle',
            tollgate_id=tollgate.id,
            lane_number='Lane 1',
            payment_method='Toll Account / E-Tag',
            actor_email='operator@tollgate.gov.zm'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'SUCCESSFUL')
        self.assertEqual(result['fee'], 20.00)
        self.assertEqual(result['balance_before'], initial_balance)
        self.assertEqual(result['balance_after'], initial_balance - 20.00)
        self.assertEqual(result['barrier_action'], 'OPEN')
        
        # Verify transaction saved in database
        tx = Transaction.query.filter_by(transaction_ref=result['transaction_ref']).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.vehicle_reg, 'ABC 1234')
        self.assertEqual(float(tx.amount), 20.00)
        
        # Verify audit log saved
        audit = AuditLog.query.filter_by(reference_id=result['transaction_ref']).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, 'TOLL_PAYMENT_SUCCESS')

    def test_05_insufficient_balance_handling(self):
        """Test vehicle with low balance triggers insufficient funds status."""
        tollgate = Tollgate.query.first()
        # BLZ 8899 is a Medium Vehicle (fee K50) with only K15 in account
        result = process_toll_payment(
            vehicle_reg='BLZ 8899',
            vehicle_type='Medium Vehicle',
            tollgate_id=tollgate.id,
            lane_number='Lane 2',
            payment_method='Toll Account / E-Tag'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'INSUFFICIENT_FUNDS')
        self.assertTrue(result['can_use_mobile_money'])
        self.assertEqual(result['fee'], 50.00)

    def test_06_simulated_mobile_money_payment(self):
        """Test paying via simulated Mobile Money after insufficient balance."""
        tollgate = Tollgate.query.first()
        result = process_toll_payment(
            vehicle_reg='BLZ 8899',
            vehicle_type='Medium Vehicle',
            tollgate_id=tollgate.id,
            lane_number='Lane 2',
            payment_method='Airtel Money'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'SUCCESSFUL')
        self.assertEqual(result['payment_method'], 'Airtel Money')
        self.assertEqual(result['barrier_action'], 'OPEN')

    def test_07_wallet_topup(self):
        """Test funding a motorist toll account."""
        motorist = User.query.filter_by(email='motorist@test.zm').first()
        account = TollAccount.query.filter_by(user_id=motorist.id).first()
        bal_before = float(account.balance)
        
        # Deposit K100
        account.deposit(100.00)
        db.session.commit()
        
        account_refreshed = TollAccount.query.get(account.id)
        self.assertEqual(float(account_refreshed.balance), bal_before + 100.00)

    def test_08_password_hashing_and_auth(self):
        """Test secure password hashing."""
        admin = User.query.filter_by(email='admin@tollgate.gov.zm').first()
        self.assertTrue(admin.check_password('Admin@123'))
        self.assertFalse(admin.check_password('WrongPassword'))

    def test_09_api_endpoints(self):
        """Test REST API responses."""
        res_rates = self.client.get('/api/v1/rates')
        self.assertEqual(res_rates.status_code, 200)
        self.assertEqual(res_rates.json['currency'], 'K')
        
        res_gates = self.client.get('/api/v1/tollgates')
        self.assertEqual(res_gates.status_code, 200)
        self.assertGreaterEqual(len(res_gates.json), 1)

    def test_10_html_views(self):
        """Test main navigation pages render successfully."""
        routes = ['/', '/simulation', '/transactions', '/modules']
        for r in routes:
            response = self.client.get(r)
            self.assertEqual(response.status_code, 200, f"Route {r} failed")

if __name__ == '__main__':
    unittest.main()
