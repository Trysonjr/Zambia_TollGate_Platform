import datetime
from app import create_app
from database import db
from models import User, TollAccount, Vehicle, Tollgate, Transaction, Payment, AuditLog

def seed_database():
    app = create_app()
    with app.app_context():
        print("[INIT] Creating database tables...")
        db.create_all()
        
        # 1. Seed Zambian Toll Plazas
        tollgates_data = [
            {'name': 'Lusaka East Toll Plaza', 'code': 'TP-LUS-01', 'location': 'Great East Road, Chongwe District', 'province': 'Lusaka Province', 'lanes': 6},
            {'name': 'Shimabala Toll Plaza', 'code': 'TP-KAF-02', 'location': 'Great North/Kafue Road, Kafue', 'province': 'Lusaka Province', 'lanes': 4},
            {'name': 'Katuba Toll Plaza', 'code': 'TP-KAT-03', 'location': 'Great North Road, Chibombo', 'province': 'Central Province', 'lanes': 4},
            {'name': 'Chongwe Toll Plaza', 'code': 'TP-CHO-04', 'location': 'Great East Road, Chongwe', 'province': 'Lusaka Province', 'lanes': 4},
            {'name': 'Manyumbi Toll Plaza', 'code': 'TP-MAN-05', 'location': 'Great North Road, Kapiri Mposhi', 'province': 'Central Province', 'lanes': 4},
            {'name': 'Michael Chilufya Sata Plaza', 'code': 'TP-NDO-06', 'location': 'Ndola-Kitwe Dual Carriageway', 'province': 'Copperbelt Province', 'lanes': 6},
            {'name': 'Kafulafuta Toll Plaza', 'code': 'TP-KAF-07', 'location': 'Kapiri-Ndola Road, Masaiti', 'province': 'Copperbelt Province', 'lanes': 4},
        ]
        
        for tg_data in tollgates_data:
            if not Tollgate.query.filter_by(name=tg_data['name']).first():
                tg = Tollgate(
                    name=tg_data['name'],
                    code=tg_data['code'],
                    location=tg_data['location'],
                    province=tg_data['province'],
                    lanes_count=tg_data['lanes'],
                    status='OPERATIONAL'
                )
                db.session.add(tg)
        db.session.commit()
        print(f"[INIT] Zambian Toll Plazas verified ({len(tollgates_data)} plazas).")
        
        # 2. Seed Administrator Account
        admin = User.query.filter_by(email='admin@tollgate.gov.zm').first()
        if not admin:
            admin = User(
                full_name='NRFA System Administrator',
                email='admin@tollgate.gov.zm',
                phone='+260971000001',
                role='admin'
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("[INIT] Created Default Administrator: admin@tollgate.gov.zm / Admin@123")
            
        # 3. Seed Demo Motorist 1 (Chileshe Mwewa - Has K150 balance for ABC 1234)
        motorist1 = User.query.filter_by(email='motorist@test.zm').first()
        if not motorist1:
            motorist1 = User(
                full_name='Chileshe Mwewa',
                email='motorist@test.zm',
                phone='+260977123456',
                role='motorist'
            )
            motorist1.set_password('Motorist@123')
            db.session.add(motorist1)
            db.session.flush()
            
            acc1 = TollAccount(
                user_id=motorist1.id,
                account_number='NRFA-ACC-1001',
                balance=150.00,
                status='ACTIVE'
            )
            db.session.add(acc1)
            
            # Vehicle ABC 1234 (Light Vehicle - Toyota Hilux)
            veh1 = Vehicle(
                user_id=motorist1.id,
                registration_number='ABC 1234',
                vehicle_type='Light Vehicle',
                make_model='Toyota Hilux 2.8 GD-6',
                rfid_tag='TAG-001',
                status='ACTIVE'
            )
            # Vehicle ALZ 5522 (Heavy Vehicle - Scania Intercity Bus)
            veh2 = Vehicle(
                user_id=motorist1.id,
                registration_number='ALZ 5522',
                vehicle_type='Heavy Vehicle',
                make_model='Scania Touring Coach',
                rfid_tag='TAG-003',
                status='ACTIVE'
            )
            db.session.add(veh1)
            db.session.add(veh2)
            db.session.commit()
            print("[INIT] Created Demo Motorist 1: motorist@test.zm (Vehicle: ABC 1234, Balance: K150.00)")
            
        # 4. Seed Demo Motorist 2 (Kondwani Banda - Low balance K15 to demo Insufficient Funds)
        motorist2 = User.query.filter_by(email='kondwani@test.zm').first()
        if not motorist2:
            motorist2 = User(
                full_name='Kondwani Banda',
                email='kondwani@test.zm',
                phone='+260966789012',
                role='motorist'
            )
            motorist2.set_password('Motorist@123')
            db.session.add(motorist2)
            db.session.flush()
            
            acc2 = TollAccount(
                user_id=motorist2.id,
                account_number='NRFA-ACC-1002',
                balance=15.00, # K15 is less than K50 medium fee!
                status='ACTIVE'
            )
            db.session.add(acc2)
            
            # Vehicle BLZ 8899 (Medium Vehicle - Mitsubishi Canter)
            veh3 = Vehicle(
                user_id=motorist2.id,
                registration_number='BLZ 8899',
                vehicle_type='Medium Vehicle',
                make_model='Mitsubishi Canter 4-Tonne',
                rfid_tag='TAG-002',
                status='ACTIVE'
            )
            db.session.add(veh3)
            db.session.commit()
            print("[INIT] Created Demo Motorist 2: kondwani@test.zm (Vehicle: BLZ 8899, Low Balance: K15.00)")

        # 5. Seed Initial Audit Log & Initial Baseline Transactions
        if Transaction.query.count() == 0:
            lusaka_east = Tollgate.query.filter_by(name='Lusaka East Toll Plaza').first()
            shimabala = Tollgate.query.filter_by(name='Shimabala Toll Plaza').first()
            
            t1 = Transaction(
                transaction_ref='TXN-ZM-INIT-001',
                vehicle_reg='ABC 1234',
                vehicle_type='Light Vehicle',
                tollgate_id=lusaka_east.id if lusaka_east else 1,
                lane_number='Lane 1',
                amount=20.00,
                payment_method='Toll Account / E-Tag',
                status='SUCCESSFUL',
                balance_before=170.00,
                balance_after=150.00,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=3)
            )
            t2 = Transaction(
                transaction_ref='TXN-ZM-INIT-002',
                vehicle_reg='ALZ 5522',
                vehicle_type='Heavy Vehicle',
                tollgate_id=shimabala.id if shimabala else 2,
                lane_number='Lane 2',
                amount=100.00,
                payment_method='Airtel Money',
                status='SUCCESSFUL',
                balance_before=None,
                balance_after=None,
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            )
            db.session.add(t1)
            db.session.add(t2)
            
            audit_init = AuditLog(
                action='SYSTEM_INITIALIZED',
                actor_email='admin@tollgate.gov.zm',
                reference_id='INIT-BOOT-001',
                details='System tables seeded with standard Zambian national toll plazas and demo datasets.',
                ip_address='127.0.0.1'
            )
            db.session.add(audit_init)
            db.session.commit()
            print("[INIT] Initial baseline transactions and audit trail logged.")
            
        print("=" * 65)
        print(" DATABASE INITIALIZATION COMPLETE!")
        print(" Active Engine: %s" % app.config.get('ACTIVE_DB_ENGINE'))
        print(" Demo Credentials:")
        print("   Administrator : admin@tollgate.gov.zm  / Admin@123")
        print("   Motorist 1    : motorist@test.zm      / Motorist@123 (ABC 1234, K150)")
        print("   Motorist 2    : kondwani@test.zm      / Motorist@123 (BLZ 8899, K15)")
        print("=" * 65)

if __name__ == '__main__':
    seed_database()
