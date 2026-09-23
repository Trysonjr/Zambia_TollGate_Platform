from flask import Blueprint, render_template

modules_bp = Blueprint('modules', __name__)

FUTURE_MODULES = [
    {
        'id': 'real_anpr',
        'title': 'Real ANPR Camera Recognition',
        'category': 'Edge Hardware & Vision',
        'icon': 'fa-camera',
        'badge': 'Prototype / Future Implementation',
        'description': 'Integration with high-speed roadside optical character recognition cameras (e.g., Hikvision / Dahua ANPR) with infrared strobe for night plate capture and deep learning character segmentation.',
        'tech_stack': 'YOLOv10 / OpenCV / RTSP Streaming / On-edge Coral TPU',
        'readiness': 'Architected (Simulated in Prototype via Manual Plate Recognition)'
    },
    {
        'id': 'real_rfid',
        'title': 'Real RFID / DSRC Hardware Transceiver',
        'category': 'IoT & Radio Frequency',
        'icon': 'fa-rss',
        'badge': 'Prototype / Future Implementation',
        'description': 'Dedicated Short Range Communication (DSRC) 5.8 GHz & UHF EPC Gen2 (860-960 MHz) readers mounted on gantry poles for windshield transponder interrogation at up to 80 km/h.',
        'tech_stack': 'ISO 18000-6C / Wiegand-to-RS485 converters / Modbus TCP',
        'readiness': 'Architected (Simulated via Virtual Windshield Tag Scanning)'
    },
    {
        'id': 'physical_barrier',
        'title': 'Physical Automatic Barrier Relay & Loop Detector',
        'category': 'Industrial Automation',
        'icon': 'fa-road-barrier',
        'badge': 'Prototype / Future Implementation',
        'description': 'Direct PLC/microcontroller relay control for heavy-duty brushless DC boom barriers (0.9s opening speed) integrated with inductive ground loop vehicle sensors and safety light curtains.',
        'tech_stack': 'Siemens S7-1200 PLC / MQTT Relay / Ground Inductive Loops',
        'readiness': 'Architected (Simulated via Interactive CSS/SVG Boom Gate Animation)'
    },
    {
        'id': 'airtel_money',
        'title': 'Direct Airtel Money API Gateway',
        'category': 'Fintech & Payments',
        'icon': 'fa-money-bill-wave',
        'badge': 'Prototype / Future Implementation',
        'description': 'Direct B2B merchant integration with Airtel Money Open API for USSD push prompts (Collection API) and instant webhook callbacks to enable automated toll fee settlement.',
        'tech_stack': 'Airtel Money Open API v2 / HMAC-SHA256 / OAuth 2.0',
        'readiness': 'Architected (Simulated via Direct Balance Deduction & Demo Fallback)'
    },
    {
        'id': 'mtn_momo',
        'title': 'MTN MoMo API Integration',
        'category': 'Fintech & Payments',
        'icon': 'fa-mobile-screen',
        'badge': 'Prototype / Future Implementation',
        'description': 'MTN Mobile Money Collections API for motorist instant checkout using registered Zambian MTN MSISDN numbers with real-time financial reconciliation.',
        'tech_stack': 'MTN MoMo API / Subscription Keys / Webhooks',
        'readiness': 'Architected (Simulated with Instant Authorization Trigger)'
    },
    {
        'id': 'zamtel_money',
        'title': 'Zamtel Kwacha Payment Gateway',
        'category': 'Fintech & Payments',
        'icon': 'fa-wallet',
        'badge': 'Prototype / Future Implementation',
        'description': 'National telecommunication carrier payment gateway integration for Zamtel Kwacha mobile subscribers.',
        'tech_stack': 'Zamtel Merchant API / XML-RPC / REST',
        'readiness': 'Architected (Simulated via Portal Top-up & Toll Settlement)'
    },
    {
        'id': 'national_account',
        'title': 'National Electronic Toll Account (NRFA / RTSA Sync)',
        'category': 'National Infrastructure',
        'icon': 'fa-id-card',
        'badge': 'Prototype / Future Implementation',
        'description': 'Unified electronic toll clearinghouse interfacing with Road Transport and Safety Agency (RTSA) e-ZamTIS vehicle registry and National Road Fund Agency (NRFA).',
        'tech_stack': 'Government Service Bus / SOAP & JSON Gateway / X-Road',
        'readiness': 'Architected (Demonstrated with Simulated Motorist Accounts)'
    },
    {
        'id': 'qr_payments',
        'title': 'Dynamic QR-Code Toll Payments',
        'category': 'Fintech & UI',
        'icon': 'fa-qrcode',
        'badge': 'Prototype / Future Implementation',
        'description': 'Dynamic lane display of EMVCo compliant QR codes on roadside digital displays allowing motorists to scan with banking apps (Absa, Stanbic, Zanaco) for instant toll clearance.',
        'tech_stack': 'EMVCo QR Standard / ISO 8583 / National Switch (Zamlink)',
        'readiness': 'Architected (Conceptual Blueprint in Place)'
    },
    {
        'id': 'offline_sync',
        'title': 'Offline Tollgate Synchronization Engine',
        'category': 'Resilience & Distributed Systems',
        'icon': 'fa-rotate',
        'badge': 'Prototype / Future Implementation',
        'description': 'Edge database replication enabling remote rural toll plazas (e.g., Luapula, Western Province) to operate autonomously during grid/fiber cuts and sync transactions upon link restoration.',
        'tech_stack': 'SQLite Edge DB / SymmetricDS / Apache Kafka / gRPC',
        'readiness': 'Architected (Dual-engine support established in codebase)'
    },
    {
        'id': 'encryption_infra',
        'title': 'Hardware Security & End-to-End Encryption',
        'category': 'Cybersecurity',
        'icon': 'fa-shield-halved',
        'badge': 'Prototype / Future Implementation',
        'description': 'Hardware Security Modules (HSM) for transaction signing, vehicle tag mutual authentication, and AES-256-GCM data transmission across national toll corridors.',
        'tech_stack': 'FIPS 140-2 Level 3 HSM / PKI / Mutual TLS (mTLS)',
        'readiness': 'Architected (Bcrypt/Scrypt hashing and secure sessions implemented)'
    },
    {
        'id': 'multiple_tollgates',
        'title': 'Full National Multi-Plaza Network',
        'category': 'Infrastructure Expansion',
        'icon': 'fa-map-location-dot',
        'badge': 'Prototype / Future Implementation',
        'description': 'Centralized real-time orchestration across all 40+ planned and gazetted national toll plazas across Zambia’s ten provinces.',
        'tech_stack': 'Distributed Cluster / Multi-Region HA / Geo-DNS',
        'readiness': 'Core Plazas (Lusaka East, Shimabala, Katuba, etc.) implemented'
    },
    {
        'id': 'cloud_deployment',
        'title': 'Government Cloud Infrastructure (Smart Zambia G-Cloud)',
        'category': 'DevOps & Cloud',
        'icon': 'fa-cloud',
        'badge': 'Prototype / Future Implementation',
        'description': 'High-availability deployment on Government Enterprise Cloud (G-Cloud) or Sovereign Zambian data centers with automated autoscaling and disaster recovery.',
        'tech_stack': 'Kubernetes (K8s) / Terraform / Docker / Nginx Ingress',
        'readiness': 'Packaged for Local Demonstration and Container Readiness'
    },
    {
        'id': 'sms_notifications',
        'title': 'Real-Time SMS & WhatsApp Alerts',
        'category': 'Motorist Communications',
        'icon': 'fa-comment-sms',
        'badge': 'Prototype / Future Implementation',
        'description': 'Instant automated SMS receipts, low-balance warnings, and abnormal vehicle transit alerts via Zambian SMS aggregators (e.g., AfricasTalking, SMSGH).',
        'tech_stack': 'SMPP Protocol / REST SMS Gateway / Twilio',
        'readiness': 'Architected (Audit logs maintain notification payloads)'
    },
    {
        'id': 'mobile_app',
        'title': 'Native Cross-Platform Motorist App',
        'category': 'Mobile Applications',
        'icon': 'fa-mobile',
        'badge': 'Prototype / Future Implementation',
        'description': 'Dedicated Flutter/React Native application for motorists featuring biometric login, GPS-based toll plaza proximity alerts, digital receipts, and one-tap wallet top-up.',
        'tech_stack': 'Flutter / Dart / Firebase Cloud Messaging / Biometric Auth',
        'readiness': 'Responsive Mobile Web UI fully functional in prototype'
    },
    {
        'id': 'advanced_analytics',
        'title': 'Predictive Traffic & Revenue Analytics',
        'category': 'Big Data & Intelligence',
        'icon': 'fa-chart-line',
        'badge': 'Prototype / Future Implementation',
        'description': 'Machine learning models predicting weekend holiday congestion on Great North Road and Kafue corridor, seasonal freight volumes, and automated revenue leak detection.',
        'tech_stack': 'Apache Spark / BigQuery / Scikit-Learn / Prophet',
        'readiness': 'Admin Analytics Dashboard with live charts implemented'
    },
    {
        'id': 'national_monitoring',
        'title': 'National Operations Control Centre (NOCC)',
        'category': 'Central Surveillance',
        'icon': 'fa-tower-broadcast',
        'badge': 'Prototype / Future Implementation',
        'description': 'Centralized 24/7 video wall dashboard in Lusaka displaying CCTV feeds, live lane throughput, red-alert lane blockages, and automated incident escalation.',
        'tech_stack': 'WebRTC / WebSockets / Grafana / Leaflet GIS',
        'readiness': 'Architected (Real-time Plaza status cards implemented)'
    },
    {
        'id': 'blacklist_mgmt',
        'title': 'Automated Stolen Vehicle & Blacklist Interception',
        'category': 'Law Enforcement Interop',
        'icon': 'fa-triangle-exclamation',
        'badge': 'Prototype / Future Implementation',
        'description': 'Real-time synchronization with Zambia Police Service stolen vehicle registry; triggers automatic boom barrier lock-down and silent dispatch alerts on flagged plates.',
        'tech_stack': 'INTERPOL Stolen Motor Vehicle (SMV) API / Webhook Alerts',
        'readiness': 'Database schema contains vehicle blacklist status flags'
    },
    {
        'id': 'ai_traffic_analysis',
        'title': 'AI-Based Axle & Classification Vision',
        'category': 'Artificial Intelligence',
        'icon': 'fa-brain',
        'badge': 'Prototype / Future Implementation',
        'description': 'Stereo vision AI models counting vehicle axles, height profiling, and verifying vehicle class against registration records to prevent revenue under-declaration.',
        'tech_stack': 'TensorFlow / PyTorch / 3D LiDAR Point Clouds / Edge AI',
        'readiness': 'Architected (Automatic fee categorization logic implemented)'
    }
]

@modules_bp.route('/modules')
def system_modules():
    return render_template('future_modules.html', modules=FUTURE_MODULES)
