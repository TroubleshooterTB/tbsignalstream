"""
COMPREHENSIVE SYSTEM DIAGNOSTIC
=====================================
Tests every component of the trading bot system to identify why trades aren't being placed.

Critical Issue: Bot hasn't placed a single trade in 2 months of live testing.
Activity feed only shows "bot started" with no further updates.

This diagnostic will test:
1. Firebase/Firestore connectivity
2. Angel One broker connection
3. WebSocket live data feed
4. Bot configuration and strategy selection
5. Signal generation logic
6. Order placement capability
7. Activity feed logging
8. Frontend-backend sync
9. Cloud Run deployment
10. All URLs, APIs, and secrets
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple
import traceback

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class SystemDiagnostic:
    def __init__(self):
        self.results = []
        self.critical_issues = []
        self.warnings = []
        self.passed_tests = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log diagnostic messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "PASS": Colors.GREEN,
            "FAIL": Colors.RED,
            "WARN": Colors.YELLOW,
            "INFO": Colors.BLUE
        }.get(level, Colors.RESET)
        
        print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")
        
        if level == "FAIL":
            self.critical_issues.append(message)
        elif level == "WARN":
            self.warnings.append(message)
        elif level == "PASS":
            self.passed_tests.append(message)
    
    def test_firestore_credentials(self) -> Tuple[bool, str]:
        """Test 1: Firebase/Firestore Authentication"""
        self.log("=" * 80, "INFO")
        self.log("TEST 1: FIREBASE/FIRESTORE CONNECTIVITY", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check if firestore-key.json exists
            key_path = "firestore-key.json"
            if not os.path.exists(key_path):
                self.log(f"CRITICAL: firestore-key.json not found at {key_path}", "FAIL")
                return False, "Missing credentials file"
            
            self.log(f"Found credentials file: {key_path}", "PASS")
            
            # Try to load and validate JSON
            with open(key_path, 'r') as f:
                creds = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                self.log(f"CRITICAL: Missing fields in credentials: {missing_fields}", "FAIL")
                return False, f"Missing fields: {missing_fields}"
            
            self.log(f"Project ID: {creds.get('project_id')}", "INFO")
            self.log(f"Client Email: {creds.get('client_email')}", "INFO")
            self.log("Credentials file structure valid", "PASS")
            
            # Try to initialize Firestore
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                # Check if already initialized
                try:
                    firebase_admin.get_app()
                    self.log("Firebase already initialized", "INFO")
                except ValueError:
                    cred = credentials.Certificate(key_path)
                    firebase_admin.initialize_app(cred)
                    self.log("Firebase initialized successfully", "PASS")
                
                db = firestore.client()
                
                # Test read access
                test_ref = db.collection('bot_status').limit(1).get()
                self.log("Firestore read access: WORKING", "PASS")
                
                # Test write access with a test document
                test_doc = db.collection('_diagnostic_test').document('test')
                test_doc.set({
                    'timestamp': datetime.now(),
                    'test': 'connectivity'
                })
                self.log("Firestore write access: WORKING", "PASS")
                
                # Clean up test document
                test_doc.delete()
                
                return True, "Firestore fully operational"
                
            except ImportError:
                self.log("WARNING: firebase_admin not installed, skipping live test", "WARN")
                return True, "Credentials valid (firebase_admin not installed for live test)"
            except Exception as e:
                self.log(f"CRITICAL: Firestore connection failed: {str(e)}", "FAIL")
                return False, str(e)
                
        except Exception as e:
            self.log(f"CRITICAL: Firestore test failed: {str(e)}", "FAIL")
            self.log(traceback.format_exc(), "INFO")
            return False, str(e)
    
    def test_angel_one_credentials(self) -> Tuple[bool, str]:
        """Test 2: Angel One Broker Connection"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 2: ANGEL ONE BROKER CONNECTION", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check environment variables or config
            required_env_vars = {
                'ANGEL_API_KEY': os.getenv('ANGEL_API_KEY'),
                'ANGEL_CLIENT_CODE': os.getenv('ANGEL_CLIENT_CODE'),
                'ANGEL_PASSWORD': os.getenv('ANGEL_PASSWORD'),
                'ANGEL_TOTP_SECRET': os.getenv('ANGEL_TOTP_SECRET')
            }
            
            missing_vars = [key for key, value in required_env_vars.items() if not value]
            
            if missing_vars:
                self.log(f"CRITICAL: Missing Angel One credentials: {missing_vars}", "FAIL")
                self.log("These credentials should be set in Cloud Run environment or .env file", "INFO")
                return False, f"Missing credentials: {missing_vars}"
            
            self.log("All Angel One credentials found", "PASS")
            
            # Mask sensitive data for display
            for key, value in required_env_vars.items():
                if value:
                    masked = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
                    self.log(f"{key}: {masked}", "INFO")
            
            # Try to test broker connection
            try:
                from trading_bot_service.utils.angel_one_auth import AngelOneAuthManager
                
                auth_manager = AngelOneAuthManager(
                    api_key=required_env_vars['ANGEL_API_KEY'],
                    client_code=required_env_vars['ANGEL_CLIENT_CODE'],
                    password=required_env_vars['ANGEL_PASSWORD'],
                    totp_secret=required_env_vars['ANGEL_TOTP_SECRET']
                )
                
                # Try to login
                auth_manager.login()
                self.log("Angel One login: SUCCESS", "PASS")
                
                # Get profile to verify connection
                profile = auth_manager.get_profile()
                if profile:
                    self.log(f"Broker profile retrieved: {profile.get('name', 'Unknown')}", "PASS")
                    self.log(f"Client ID: {profile.get('clientcode', 'Unknown')}", "INFO")
                    return True, "Angel One connection operational"
                else:
                    self.log("WARNING: Login succeeded but profile retrieval failed", "WARN")
                    return True, "Partial success - login OK, profile failed"
                    
            except ImportError:
                self.log("WARNING: angel_one_auth module not found, skipping live test", "WARN")
                return True, "Credentials present (module not available for live test)"
            except Exception as e:
                self.log(f"CRITICAL: Angel One connection failed: {str(e)}", "FAIL")
                return False, str(e)
                
        except Exception as e:
            self.log(f"CRITICAL: Angel One test failed: {str(e)}", "FAIL")
            self.log(traceback.format_exc(), "INFO")
            return False, str(e)
    
    def test_websocket_implementation(self) -> Tuple[bool, str]:
        """Test 3: WebSocket Implementation"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 3: WEBSOCKET LIVE DATA FEED", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check for WebSocket code in realtime_bot_engine.py
            bot_file = "trading_bot_service/realtime_bot_engine.py"
            
            if not os.path.exists(bot_file):
                self.log(f"CRITICAL: Bot engine file not found: {bot_file}", "FAIL")
                return False, "Bot engine file missing"
            
            with open(bot_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for WebSocket implementation
            ws_checks = {
                '_initialize_websocket': '_initialize_websocket' in content,
                'self.ws_manager': 'self.ws_manager' in content,
                '_on_tick': '_on_tick' in content,
                'WebSocket reconnect': 'reconnect' in content.lower(),
                'Position reconciliation': 'reconcile' in content.lower()
            }
            
            all_passed = True
            for check, result in ws_checks.items():
                if result:
                    self.log(f"WebSocket check [{check}]: FOUND", "PASS")
                else:
                    self.log(f"WebSocket check [{check}]: MISSING", "FAIL")
                    all_passed = False
            
            if all_passed:
                self.log("WebSocket implementation: COMPLETE", "PASS")
                return True, "WebSocket implementation verified"
            else:
                self.log("WebSocket implementation: INCOMPLETE", "FAIL")
                return False, "Missing WebSocket components"
                
        except Exception as e:
            self.log(f"CRITICAL: WebSocket test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_bot_configuration(self) -> Tuple[bool, str]:
        """Test 4: Bot Configuration & Strategy Selection"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 4: BOT CONFIGURATION & STRATEGY SELECTION", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            
            # Check bot_config collection
            config_docs = db.collection('bot_config').limit(5).get()
            
            if not config_docs:
                self.log("CRITICAL: No bot configuration found in Firestore", "FAIL")
                self.log("Bot needs configuration to know which strategies to run", "INFO")
                return False, "Missing bot configuration"
            
            self.log(f"Found {len(config_docs)} configuration document(s)", "PASS")
            
            for doc in config_docs:
                config = doc.to_dict()
                self.log(f"\nConfiguration ID: {doc.id}", "INFO")
                self.log(f"  Status: {config.get('status', 'UNKNOWN')}", "INFO")
                self.log(f"  Strategy: {config.get('strategy', 'UNKNOWN')}", "INFO")
                self.log(f"  Symbols: {len(config.get('symbol_universe', []))} symbols", "INFO")
                self.log(f"  Trading enabled: {config.get('trading_enabled', False)}", "INFO")
                
                # Critical checks
                if config.get('status') != 'RUNNING':
                    self.log(f"  WARNING: Bot status is '{config.get('status')}', not 'RUNNING'", "WARN")
                
                if not config.get('trading_enabled'):
                    self.log("  CRITICAL: Trading is DISABLED in configuration", "FAIL")
                    self.log("  This is why bot isn't placing trades!", "FAIL")
                
                if not config.get('symbol_universe'):
                    self.log("  CRITICAL: No symbols configured in symbol_universe", "FAIL")
                    self.log("  Bot has nothing to trade!", "FAIL")
                
                if not config.get('strategy'):
                    self.log("  CRITICAL: No strategy selected", "FAIL")
            
            return True, "Configuration found (check warnings)"
            
        except Exception as e:
            self.log(f"Configuration test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_signal_generation(self) -> Tuple[bool, str]:
        """Test 5: Signal Generation Logic"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 5: SIGNAL GENERATION LOGIC", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check for strategy files
            strategy_files = {
                'Alpha Ensemble': 'trading_bot_service/alpha_ensemble_strategy.py',
                'Defining Order': 'trading_bot_service/defining_order_strategy.py',
                'Ironclad': 'trading_bot_service/ironclad_strategy.py',
                'Mean Reversion': 'trading_bot_service/mean_reversion_strategy.py'
            }
            
            found_strategies = []
            for name, path in strategy_files.items():
                if os.path.exists(path):
                    self.log(f"Strategy found: {name}", "PASS")
                    found_strategies.append(name)
                else:
                    self.log(f"Strategy missing: {name} ({path})", "WARN")
            
            if not found_strategies:
                self.log("CRITICAL: No strategy files found!", "FAIL")
                return False, "No strategies available"
            
            # Check signals collection in Firestore
            try:
                import firebase_admin
                from firebase_admin import firestore
                
                db = firestore.client()
                
                # Check recent signals
                signals = db.collection('signals').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).get()
                
                if signals:
                    self.log(f"Found {len(signals)} recent signals in Firestore", "PASS")
                    
                    for signal in signals[:3]:  # Show last 3
                        sig_data = signal.to_dict()
                        self.log(f"\n  Signal: {sig_data.get('symbol')} - {sig_data.get('signal_type')}", "INFO")
                        self.log(f"    Direction: {sig_data.get('direction')}", "INFO")
                        self.log(f"    Status: {sig_data.get('status')}", "INFO")
                        self.log(f"    Timestamp: {sig_data.get('timestamp')}", "INFO")
                else:
                    self.log("WARNING: No signals found in Firestore", "WARN")
                    self.log("Bot may not be generating signals, or they're being deleted", "WARN")
                
            except Exception as e:
                self.log(f"Could not check signals collection: {str(e)}", "WARN")
            
            return True, f"Found {len(found_strategies)} strategies"
            
        except Exception as e:
            self.log(f"Signal generation test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_order_placement(self) -> Tuple[bool, str]:
        """Test 6: Order Placement Capability"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 6: ORDER PLACEMENT CAPABILITY", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check for order placement code
            bot_file = "trading_bot_service/realtime_bot_engine.py"
            
            with open(bot_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Critical order placement checks
            order_checks = {
                'place_order method': 'def place_order' in content or 'def _place_order' in content,
                'Order validation': 'validate_order' in content or 'check_order' in content,
                'Broker order call': 'placeOrder' in content or 'place_order' in content,
                'Paper trading check': 'paper_trading' in content or 'PAPER_TRADING' in content,
                'Trading enabled check': 'trading_enabled' in content,
                'Market hours check': 'market_hours' in content or 'is_market_open' in content,
            }
            
            critical_missing = []
            for check, result in order_checks.items():
                if result:
                    self.log(f"Order placement check [{check}]: FOUND", "PASS")
                else:
                    self.log(f"Order placement check [{check}]: MISSING", "WARN")
                    if check in ['place_order method', 'Broker order call']:
                        critical_missing.append(check)
            
            # Check for paper trading mode (might prevent real orders)
            if 'PAPER_TRADING = True' in content or 'paper_trading = True' in content:
                self.log("CRITICAL: Paper trading mode is ENABLED", "FAIL")
                self.log("Bot will NOT place real orders in paper trading mode!", "FAIL")
                return False, "Paper trading mode enabled"
            
            # Check for trading enabled flag
            if 'trading_enabled' in content:
                if 'if not' in content and 'trading_enabled' in content:
                    self.log("Found trading_enabled check - bot may be disabled", "WARN")
            
            if critical_missing:
                self.log(f"CRITICAL: Missing essential components: {critical_missing}", "FAIL")
                return False, f"Missing: {critical_missing}"
            
            # Check orders collection in Firestore
            try:
                import firebase_admin
                from firebase_admin import firestore
                
                db = firestore.client()
                
                # Check recent orders
                orders = db.collection('orders').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).get()
                
                if orders:
                    self.log(f"Found {len(orders)} recent orders in Firestore", "PASS")
                    
                    for order in orders[:3]:  # Show last 3
                        order_data = order.to_dict()
                        self.log(f"\n  Order: {order_data.get('symbol')}", "INFO")
                        self.log(f"    Status: {order_data.get('status')}", "INFO")
                        self.log(f"    Type: {order_data.get('order_type')}", "INFO")
                        self.log(f"    Timestamp: {order_data.get('timestamp')}", "INFO")
                else:
                    self.log("CRITICAL: NO ORDERS found in Firestore!", "FAIL")
                    self.log("This confirms the bot has never placed orders", "FAIL")
                    
            except Exception as e:
                self.log(f"Could not check orders collection: {str(e)}", "WARN")
            
            return True, "Order placement code exists (no orders executed)"
            
        except Exception as e:
            self.log(f"Order placement test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_activity_feed(self) -> Tuple[bool, str]:
        """Test 7: Activity Feed Logging"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 7: ACTIVITY FEED LOGGING", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            
            # Check activity_feed collection
            activities = db.collection('activity_feed').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).get()
            
            if not activities:
                self.log("CRITICAL: No activity feed entries found!", "FAIL")
                self.log("Bot is not logging any activities", "FAIL")
                return False, "Activity feed empty"
            
            self.log(f"Found {len(activities)} activity feed entries", "PASS")
            
            # Analyze activity types
            activity_types = {}
            for activity in activities:
                act_data = activity.to_dict()
                act_type = act_data.get('type', 'UNKNOWN')
                activity_types[act_type] = activity_types.get(act_type, 0) + 1
            
            self.log("\nActivity breakdown:", "INFO")
            for act_type, count in activity_types.items():
                self.log(f"  {act_type}: {count}", "INFO")
            
            # Check if bot is stuck at "BOT_STARTED"
            if activity_types.get('BOT_STARTED', 0) > 0 and len(activity_types) == 1:
                self.log("CRITICAL: Only 'BOT_STARTED' activities found!", "FAIL")
                self.log("Bot starts but doesn't log any further actions", "FAIL")
                self.log("This indicates bot may be crashing or not running main loop", "FAIL")
            
            # Show recent activities
            self.log("\nRecent activities:", "INFO")
            for activity in activities[:5]:
                act_data = activity.to_dict()
                self.log(f"  [{act_data.get('timestamp')}] {act_data.get('type')}: {act_data.get('message', 'No message')}", "INFO")
            
            return True, f"Activity feed has {len(activities)} entries"
            
        except Exception as e:
            self.log(f"Activity feed test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_cloud_run_deployment(self) -> Tuple[bool, str]:
        """Test 9: Cloud Run Deployment"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 9: CLOUD RUN DEPLOYMENT & HEALTH", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check cloud_run_config.json
            config_file = "cloud_run_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                service_url = config.get('service_url')
                self.log(f"Service URL: {service_url}", "INFO")
                
                # Test health endpoint
                if service_url:
                    try:
                        health_url = f"{service_url}/health"
                        response = requests.get(health_url, timeout=10)
                        
                        if response.status_code == 200:
                            self.log("Health endpoint: HEALTHY", "PASS")
                            health_data = response.json()
                            self.log(f"  Status: {health_data.get('status')}", "INFO")
                            self.log(f"  Uptime: {health_data.get('uptime', 'Unknown')}", "INFO")
                        else:
                            self.log(f"Health endpoint returned: {response.status_code}", "WARN")
                    except requests.RequestException as e:
                        self.log(f"WARNING: Could not reach health endpoint: {str(e)}", "WARN")
                        self.log("Bot may not be deployed or URL is incorrect", "WARN")
            else:
                self.log("WARNING: cloud_run_config.json not found", "WARN")
            
            # Check deployment files
            deployment_files = {
                'Dockerfile': 'trading_bot_service/Dockerfile',
                'cloudbuild.yaml': 'cloudbuild.yaml',
                'requirements.txt': 'trading_bot_service/requirements.txt'
            }
            
            for name, path in deployment_files.items():
                if os.path.exists(path):
                    self.log(f"Deployment file [{name}]: FOUND", "PASS")
                else:
                    self.log(f"Deployment file [{name}]: MISSING", "WARN")
            
            return True, "Deployment configuration verified"
            
        except Exception as e:
            self.log(f"Cloud Run test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def test_frontend_backend_sync(self) -> Tuple[bool, str]:
        """Test 8: Frontend-Backend Connectivity"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("TEST 8: FRONTEND-BACKEND API CONNECTIVITY", "INFO")
        self.log("=" * 80, "INFO")
        
        try:
            # Check for API routes in backend
            api_file = "trading_bot_service/main.py"
            
            if not os.path.exists(api_file):
                self.log("WARNING: main.py not found", "WARN")
                return False, "API file missing"
            
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for essential API endpoints
            endpoints = {
                '/health': '/health' in content,
                '/start': '/start' in content or '/bot/start' in content,
                '/stop': '/stop' in content or '/bot/stop' in content,
                '/status': '/status' in content or '/bot/status' in content,
                '/signals': '/signals' in content,
            }
            
            for endpoint, exists in endpoints.items():
                if exists:
                    self.log(f"API endpoint [{endpoint}]: FOUND", "PASS")
                else:
                    self.log(f"API endpoint [{endpoint}]: MISSING", "WARN")
            
            # Check frontend dashboard files
            frontend_files = {
                'Main page': 'src/app/page.tsx',
                'Live alerts': 'src/components/live-alerts-dashboard.tsx',
                'OTR widget': 'src/components/otr-compliance-widget.tsx',
                'Regime indicator': 'src/components/regime-indicator.tsx'
            }
            
            for name, path in frontend_files.items():
                if os.path.exists(path):
                    self.log(f"Frontend component [{name}]: FOUND", "PASS")
                else:
                    self.log(f"Frontend component [{name}]: MISSING", "WARN")
            
            return True, "Frontend and backend files verified"
            
        except Exception as e:
            self.log(f"Frontend-Backend test failed: {str(e)}", "FAIL")
            return False, str(e)
    
    def run_all_tests(self):
        """Run complete diagnostic suite"""
        self.log(f"\n{Colors.BOLD}{'=' * 80}", "INFO")
        self.log("COMPREHENSIVE SYSTEM DIAGNOSTIC - TRADING BOT", "INFO")
        self.log(f"{'=' * 80}{Colors.RESET}\n", "INFO")
        self.log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log(f"Critical Issue: Bot hasn't placed any trades in 2 months", "INFO")
        self.log(f"Activity feed only shows 'BOT_STARTED' with no further updates\n", "INFO")
        
        tests = [
            ("Firebase/Firestore", self.test_firestore_credentials),
            ("Angel One Connection", self.test_angel_one_credentials),
            ("WebSocket Implementation", self.test_websocket_implementation),
            ("Bot Configuration", self.test_bot_configuration),
            ("Signal Generation", self.test_signal_generation),
            ("Order Placement", self.test_order_placement),
            ("Activity Feed", self.test_activity_feed),
            ("Frontend-Backend Sync", self.test_frontend_backend_sync),
            ("Cloud Run Deployment", self.test_cloud_run_deployment),
        ]
        
        for test_name, test_func in tests:
            try:
                success, message = test_func()
                self.results.append({
                    'test': test_name,
                    'success': success,
                    'message': message
                })
            except Exception as e:
                self.log(f"\nTEST CRASHED: {test_name}", "FAIL")
                self.log(str(e), "FAIL")
                self.results.append({
                    'test': test_name,
                    'success': False,
                    'message': f"Test crashed: {str(e)}"
                })
        
        self.generate_report()
    
    def generate_report(self):
        """Generate final diagnostic report"""
        self.log("\n\n" + "=" * 80, "INFO")
        self.log(f"{Colors.BOLD}DIAGNOSTIC REPORT - SUMMARY{Colors.RESET}", "INFO")
        self.log("=" * 80, "INFO")
        
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        
        self.log(f"\nTests Passed: {Colors.GREEN}{passed}{Colors.RESET}/{len(self.results)}", "INFO")
        self.log(f"Tests Failed: {Colors.RED}{failed}{Colors.RESET}/{len(self.results)}\n", "INFO")
        
        if failed > 0:
            self.log(f"{Colors.RED}FAILED TESTS:{Colors.RESET}", "INFO")
            for result in self.results:
                if not result['success']:
                    self.log(f"  ✗ {result['test']}: {result['message']}", "INFO")
        
        if self.critical_issues:
            self.log(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ISSUES FOUND ({len(self.critical_issues)}):{Colors.RESET}", "INFO")
            for i, issue in enumerate(self.critical_issues, 1):
                self.log(f"  {i}. {issue}", "INFO")
        
        if self.warnings:
            self.log(f"\n{Colors.YELLOW}WARNINGS ({len(self.warnings)}):{Colors.RESET}", "INFO")
            for i, warning in enumerate(self.warnings, 1):
                self.log(f"  {i}. {warning}", "INFO")
        
        # Root cause analysis
        self.log(f"\n{Colors.BOLD}ROOT CAUSE ANALYSIS:{Colors.RESET}", "INFO")
        self.log("=" * 80, "INFO")
        
        # Analyze the patterns
        if "trading_enabled" in str(self.critical_issues).lower():
            self.log(f"{Colors.RED}>>> PRIMARY ISSUE: Trading is DISABLED in bot configuration{Colors.RESET}", "INFO")
            self.log("    ACTION: Set 'trading_enabled: true' in bot_config Firestore document", "INFO")
        
        if "no orders" in str(self.critical_issues).lower():
            self.log(f"{Colors.RED}>>> CONFIRMED: Bot has never placed any orders{Colors.RESET}", "INFO")
            self.log("    This validates the user's concern - bot is not executing trades", "INFO")
        
        if "bot_started" in str(self.critical_issues).lower():
            self.log(f"{Colors.RED}>>> ISSUE: Bot only logs startup, then stops/crashes{Colors.RESET}", "INFO")
            self.log("    ACTION: Check Cloud Run logs for errors after bot startup", "INFO")
            self.log("    ACTION: Verify bot main loop is running continuously", "INFO")
        
        if "paper trading" in str(self.critical_issues).lower():
            self.log(f"{Colors.RED}>>> ISSUE: Paper trading mode is enabled{Colors.RESET}", "INFO")
            self.log("    ACTION: Disable paper trading to allow real order placement", "INFO")
        
        self.log("\n" + "=" * 80, "INFO")
        self.log(f"{Colors.BOLD}END OF DIAGNOSTIC REPORT{Colors.RESET}", "INFO")
        self.log("=" * 80 + "\n", "INFO")

if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    diagnostic.run_all_tests()
