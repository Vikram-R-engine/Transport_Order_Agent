"""
Transportation Order Creation Agent V2
3-Layer Extraction: Regex → Gemini → Human Escalation
Optimized for minimal Gemini quota usage
Built completely from scratch
"""

import imaplib
import smtplib
import json
import re
import os
import uuid
import time
import datetime
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.parser import Parser


class TransportOrderAgent:
	"""Main agent - 3-layer extraction pipeline"""

	def __init__(self, email_config):
		"""Initialize agent with email config"""
		self.config = email_config
		self.orders_file = 'orders_database.json'
		self.exceptions_file = 'exceptions_log.json'
		self.customers_file = 'customers_database.json'
		self.processed_emails_file = 'processed_emails.json'
		self.gemini_stats_file = 'gemini_stats.json'
		
		self._initialize_data_files()
		
		# Initialize Gemini API
		GEMINI_API_KEY = "GEMINI API KEY HERE"
		genai.configure(api_key=GEMINI_API_KEY)
		self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
		
		# SLA configurations (in hours)
		self.sla_config = {
			'standard': 48,
			'express': 24,
			'same_day': 4
		}
		
		# Valid vehicle types
		self.valid_vehicle_types = [
			'sedan', 'suv', 'hatchback', 'van', 'truck',
			'tempo', 'auto', 'bike', 'cycle'
		]
		
		# Service locations
		self.service_locations = [
			'rasipuram', 'salem', 'krishnagiri', 'dharmapuri',
			'bengaluru', 'coimbatore', 'erode', 'tiruppur'
		]

	def _initialize_data_files(self):
		"""Initialize JSON databases"""
		if not os.path.exists(self.orders_file):
			with open(self.orders_file, 'w') as f:
				json.dump([], f, indent=2)
		
		if not os.path.exists(self.exceptions_file):
			with open(self.exceptions_file, 'w') as f:
				json.dump([], f, indent=2)
		
		if not os.path.exists(self.customers_file):
			sample_customers = [
				{'id': 'CUST001', 'name': 'Rajesh Kumar', 'email': 'rajesh@example.com', 'phone': '9876543210'},
				{'id': 'CUST002', 'name': 'Priya Singh', 'email': 'priya@example.com', 'phone': '9876543211'},
				{'id': 'CUST003', 'name': 'Amit Patel', 'email': 'amit@example.com', 'phone': '9876543212'},
			]
			with open(self.customers_file, 'w') as f:
				json.dump(sample_customers, f, indent=2)
		
		if not os.path.exists(self.processed_emails_file):
			with open(self.processed_emails_file, 'w') as f:
				json.dump([], f, indent=2)
		
		if not os.path.exists(self.gemini_stats_file):
			with open(self.gemini_stats_file, 'w') as f:
				json.dump({'total_calls': 0, 'successful': 0, 'failed': 0}, f, indent=2)

	def connect_imap(self):
		"""Establish IMAP connection"""
		try:
			mail = imaplib.IMAP4_SSL(self.config['imap_server'], self.config['imap_port'])
			mail.login(self.config['email'], self.config['password'])
			print(f"✓ IMAP connected as {self.config['email']}")
			return mail
		except Exception as e:
			print(f"✗ IMAP connection failed: {e}")
			return None

	def fetch_unread_emails(self, mail, limit=5):
		"""Fetch unread emails"""
		try:
			mail.select('INBOX')
			status, email_ids = mail.search(None, 'UNSEEN')
			if status != 'OK':
				return []
			
			email_ids = email_ids[0].split()[:limit]
			emails = []
			
			for email_id in email_ids:
				status, email_data = mail.fetch(email_id, '(RFC822)')
				if status == 'OK':
					emails.append((email_id, email_data[0][1]))
			
			print(f"✓ Fetched {len(emails)} unread emails")
			return emails
		except Exception as e:
			print(f"✗ Error fetching emails: {e}")
			return []

	def parse_email_body(self, email_bytes):
		"""Parse email and extract sender, subject, body"""
		try:
			parser = Parser()
			email_message = parser.parsestr(email_bytes.decode('utf-8', errors='ignore'))
			sender = email_message.get('From', 'unknown@unknown.com')
			subject = email_message.get('Subject', 'No Subject')
			
			body = ''
			if email_message.is_multipart():
				for part in email_message.walk():
					if part.get_content_type() == 'text/plain':
						body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
						break
			else:
				body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
			
			return {
				'from': sender.split('<')[-1].replace('>', '').strip() if '<' in sender else sender,
				'subject': subject,
				'body': body
			}
		except Exception as e:
			print(f"✗ Error parsing email: {e}")
			return None

	def extract_order_details(self, email_body):
		"""
		3-LAYER EXTRACTION PIPELINE:
		1. Try REGEX (free, fast) - 90% success
		2. If regex fails → Try GEMINI (quota) - 8% success
		3. If both fail → Human escalation - 2% cases
		"""
		# LAYER 1: REGEX EXTRACTION (FREE)
		regex_details = self.extract_by_regex(email_body)
		regex_score = self._score_extraction(regex_details)
		
		if regex_score >= 5:  # 5/6 fields found
			print(f"✅ LAYER 1 (Regex): {regex_score}/6 fields - Order ready")
			return regex_details
		
		print(f"⚠️  LAYER 1 (Regex): Only {regex_score}/6 fields - Trying Gemini...")
		
		# LAYER 2: GEMINI EXTRACTION (QUOTA)
		gemini_details = self.extract_by_gemini(email_body)
		gemini_score = self._score_extraction(gemini_details)
		
		if gemini_score >= 5:  # 5/6 fields found
			print(f"✅ LAYER 2 (Gemini): {gemini_score}/6 fields - Order ready")
			return gemini_details
		
		print(f"❌ LAYER 2 (Gemini): Only {gemini_score}/6 fields - Escalating to human")
		
		# LAYER 3: Return partial details for human review
		return gemini_details  # Return best effort for validation to catch

	def extract_by_regex(self, email_body):
		"""LAYER 1: Fast regex extraction (no API calls)"""
		email_lower = email_body.lower()
		
		name_match = re.search(r'(?:name|customer|from)[\s:]+([A-Za-z\s]+?)[\n,;]', email_body, re.IGNORECASE)
		pickup_match = re.search(r'(?:pickup|from|origin|start)[\s:]+([a-z]+)', email_lower)
		drop_match = re.search(r'(?:drop|to|destination|end)[\s:]+([a-z]+)', email_lower)
		vehicle_match = re.search(r'(?:vehicle|truck|car|van|tempo|auto|bike|cycle)[\s:]*(?:type)?[\s:]*(\w+)?', email_lower)
		date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})', email_body)
		qty_match = re.search(r'(?:qty|quantity|amount|items?)[\s:]*(\d+)', email_lower)
		
		return {
			'customer_name': name_match.group(1).strip().title() if name_match else None,
			'pickup_location': pickup_match.group(1).strip().lower() if pickup_match else None,
			'drop_location': drop_match.group(1).strip().lower() if drop_match else None,
			'vehicle_type': vehicle_match.group(1).strip().lower() if vehicle_match else None,
			'date': date_match.group(1) if date_match else None,
			'quantity': int(qty_match.group(1)) if qty_match else None,
			'sla': 'standard',
			'special_instructions': None,
			'raw_body': email_body,
			'extraction_method': 'regex'
		}

	def extract_by_gemini(self, email_body):
		"""LAYER 2: Smart NLP extraction (only if regex fails)"""
		try:
			prompt = f"""
Extract transportation order details from this email. Support any language.

Email content:
{email_body[:2000]}

Return ONLY valid JSON (no markdown):
{{
	"customer_name": "extracted name or null",
	"pickup_location": "extracted city or null",
	"drop_location": "extracted city or null",
	"vehicle_type": "extracted vehicle or null",
	"order_date": "DD-MM-YYYY or null",
	"quantity": "number or null"
}}

Valid locations: rasipuram, salem, krishnagiri, dharmapuri, bengaluru, coimbatore, erode, tiruppur
Valid vehicles: sedan, suv, hatchback, van, truck, tempo, auto, bike, cycle
"""
			
			response = self.gemini_model.generate_content(prompt)
			response_text = response.text.strip()
			
			# Clean markdown
			if response_text.startswith("```json"):
				response_text = response_text[7:]
			if response_text.startswith("```"):
				response_text = response_text[3:]
			if response_text.endswith("```"):
				response_text = response_text[:-3]
			response_text = response_text.strip()
			
			extracted = json.loads(response_text)
			
			# Log Gemini call
			self._log_gemini_call(success=True)
			
			return {
				'customer_name': extracted.get('customer_name', '').strip() if extracted.get('customer_name') else None,
				'pickup_location': extracted.get('pickup_location', '').strip().lower() if extracted.get('pickup_location') else None,
				'drop_location': extracted.get('drop_location', '').strip().lower() if extracted.get('drop_location') else None,
				'vehicle_type': extracted.get('vehicle_type', '').strip().lower() if extracted.get('vehicle_type') else None,
				'date': extracted.get('order_date', '').strip() if extracted.get('order_date') else None,
				'quantity': int(extracted.get('quantity', 0)) if extracted.get('quantity') else None,
				'sla': 'standard',
				'special_instructions': None,
				'raw_body': email_body,
				'extraction_method': 'gemini'
			}
		
		except Exception as e:
			print(f"⚠️  Gemini error: {str(e)[:100]}")
			self._log_gemini_call(success=False)
			# Return empty dict for Layer 3 escalation
			return {
				'customer_name': None,
				'pickup_location': None,
				'drop_location': None,
				'vehicle_type': None,
				'date': None,
				'quantity': None,
				'sla': 'standard',
				'special_instructions': None,
				'raw_body': email_body,
				'extraction_method': 'failed'
			}

	def _score_extraction(self, details):
		"""Score extraction: how many required fields found (0-6)"""
		required = ['customer_name', 'pickup_location', 'drop_location', 'vehicle_type', 'date', 'quantity']
		return sum(1 for field in required if details.get(field))

	def _log_gemini_call(self, success=True):
		"""Track Gemini API usage"""
		try:
			with open(self.gemini_stats_file, 'r') as f:
				stats = json.load(f)
			stats['total_calls'] += 1
			if success:
				stats['successful'] += 1
			else:
				stats['failed'] += 1
			with open(self.gemini_stats_file, 'w') as f:
				json.dump(stats, f, indent=2)
		except:
			pass

	def validate_order(self, order_details, sender_email):
		"""Validate extracted details"""
		errors = []
		suggestions = []
		
		if not order_details.get('customer_name'):
			errors.append('Customer name is missing')
			suggestions.append('Please provide your name')
		if not order_details.get('pickup_location'):
			errors.append('Pickup location is missing')
			suggestions.append(f'Valid locations: {", ".join(self.service_locations)}')
		if not order_details.get('drop_location'):
			errors.append('Drop location is missing')
			suggestions.append(f'Valid locations: {", ".join(self.service_locations)}')
		if not order_details.get('vehicle_type'):
			errors.append('Vehicle type is missing')
			suggestions.append(f'Valid vehicles: {", ".join(self.valid_vehicle_types)}')
		if not order_details.get('date'):
			errors.append('Order date is missing')
			suggestions.append('Please provide date in DD-MM-YYYY format')
		if not order_details.get('quantity'):
			errors.append('Quantity is missing')
			suggestions.append('Please specify quantity')
		
		if (order_details.get('pickup_location') and order_details.get('drop_location') and
			order_details['pickup_location'].lower() == order_details['drop_location'].lower()):
			errors.append('Pickup and drop cannot be the same')
			suggestions.append('Specify different locations')
		
		customer = self._find_customer_by_email(sender_email)
		if not customer:
			suggestions.append(f'New customer: {sender_email}')
		
		if self._check_duplicate_order(order_details, sender_email):
			errors.append('Duplicate order detected')
			suggestions.append('Verify this is a new request')
		
		if order_details.get('date'):
			try:
				order_date = datetime.datetime.strptime(order_details['date'], '%d-%m-%Y')
				if order_date < datetime.datetime.now():
					errors.append('Order date is in the past')
					suggestions.append('Provide a future date')
			except:
				errors.append('Invalid date format')
				suggestions.append('Use DD-MM-YYYY')
		
		is_valid = len(errors) == 0
		return is_valid, errors, suggestions

	def _find_customer_by_email(self, email):
		"""Find customer in database"""
		try:
			with open(self.customers_file, 'r') as f:
				customers = json.load(f)
			for customer in customers:
				if customer['email'].lower() == email.lower():
					return customer
		except:
			pass
		return None

	def _check_duplicate_order(self, order_details, sender_email):
		"""Check for duplicates within 1 hour"""
		try:
			with open(self.orders_file, 'r') as f:
				orders = json.load(f)
			for order in orders:
				if (order.get('sender_email') == sender_email and
					order.get('pickup_location') == order_details.get('pickup_location') and
					order.get('drop_location') == order_details.get('drop_location') and
					order.get('date') == order_details.get('date')):
					created_time = datetime.datetime.fromisoformat(order.get('created_at', '2000-01-01T00:00:00'))
					if (datetime.datetime.now() - created_time).total_seconds() < 3600:
						return True
		except:
			pass
		return False

	def create_order(self, order_details, sender_email):
		"""Create order with Job ID"""
		job_id = f"JOB-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
		order = {
			'job_id': job_id,
			'sender_email': sender_email,
			'customer_name': order_details.get('customer_name'),
			'pickup_location': order_details.get('pickup_location'),
			'drop_location': order_details.get('drop_location'),
			'vehicle_type': order_details.get('vehicle_type'),
			'date': order_details.get('date'),
			'quantity': order_details.get('quantity'),
			'sla': order_details.get('sla'),
			'special_instructions': order_details.get('special_instructions'),
			'status': 'confirmed',
			'created_at': datetime.datetime.now().isoformat(),
			'sla_deadline': self._calculate_sla_deadline(order_details.get('sla')),
			'extraction_method': order_details.get('extraction_method', 'unknown')
		}
		
		try:
			with open(self.orders_file, 'r') as f:
				orders = json.load(f)
			orders.append(order)
			with open(self.orders_file, 'w') as f:
				json.dump(orders, f, indent=2)
			print(f"✓ Order created: {job_id}")
		except Exception as e:
			print(f"✗ Error saving order: {e}")
		
		return order

	def _calculate_sla_deadline(self, sla_type):
		"""Calculate SLA deadline"""
		hours = self.sla_config.get(sla_type, 48)
		deadline = datetime.datetime.now() + datetime.timedelta(hours=hours)
		return deadline.isoformat()

	def log_exception(self, email_data, order_details, errors, suggestions, sender_email):
		"""Log exceptions for human review"""
		exception_record = {
			'timestamp': datetime.datetime.now().isoformat(),
			'sender_email': sender_email,
			'email_subject': email_data.get('subject'),
			'extracted_details': order_details,
			'validation_errors': errors,
			'ai_suggestions': suggestions,
			'status': 'pending_human_review',
			'extraction_method': order_details.get('extraction_method', 'unknown')
		}
		
		try:
			with open(self.exceptions_file, 'r') as f:
				exceptions = json.load(f)
			exceptions.append(exception_record)
			with open(self.exceptions_file, 'w') as f:
				json.dump(exceptions, f, indent=2)
			print(f"✓ Exception logged for human review")
		except Exception as e:
			print(f"✗ Error logging exception: {e}")
		
		return exception_record

	def send_acknowledgment_email(self, order):
		"""Send confirmation email"""
		try:
			msg = MIMEMultipart()
			msg['From'] = self.config['email']
			msg['To'] = order['sender_email']
			msg['Subject'] = f"Order Confirmation - Job ID: {order['job_id']}"
			
			body = f"""
Dear {order['customer_name']},

Thank you for your transportation order request!

=== ORDER CONFIRMATION ===

Job ID: {order['job_id']}
Status: {order['status'].upper()}

Order Details:
- Pickup Location: {order['pickup_location']}
- Drop Location: {order['drop_location']}
- Vehicle Type: {order['vehicle_type']}
- Order Date: {order['date']}
- Quantity: {order['quantity']}
- Service Level: {order['sla'].upper()}

SLA Deadline: {order['sla_deadline']}

Extraction Method: {order.get('extraction_method', 'automatic')}

Your order has been successfully created in our Transportation Management System.

For any queries, please reply to this email.

Best Regards,
Transportation Order Agent V2
Automated Order Processing System
"""
			
			msg.attach(MIMEText(body, 'plain'))
			
			with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
				server.starttls()
				server.login(self.config['email'], self.config['password'])
				server.send_message(msg)
			
			print(f"✓ Confirmation sent to {order['sender_email']}")
		except Exception as e:
			print(f"✗ Error sending confirmation: {e}")

	def send_exception_email(self, sender_email, customer_name, errors, suggestions, email_subject):
		"""Send exception notification"""
		try:
			msg = MIMEMultipart()
			msg['From'] = self.config['email']
			msg['To'] = sender_email
			msg['Subject'] = f"Order Review Required - {email_subject}"
			
			body = f"""
Dear {customer_name or 'Customer'},

Thank you for your order request. We need some information before processing.

=== ISSUES FOUND ===

"""
			
			for i, error in enumerate(errors, 1):
				body += f"\n{i}. {error}"
			
			body += "\n\n=== SUGGESTIONS ===\n"
			
			for i, suggestion in enumerate(suggestions, 1):
				body += f"\n{i}. {suggestion}"
			
			body += """

Please reply with the required information, and we'll process immediately.

Note: Our AI tried both fast and smart extraction. A human will review this.

Best Regards,
Transportation Order Agent V2
"""
			
			msg.attach(MIMEText(body, 'plain'))
			
			with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
				server.starttls()
				server.login(self.config['email'], self.config['password'])
				server.send_message(msg)
			
			print(f"✓ Exception notice sent to {sender_email}")
		except Exception as e:
			print(f"✗ Error sending exception email: {e}")

	def mark_email_as_processed(self, email_id):
		"""Mark email processed"""
		try:
			with open(self.processed_emails_file, 'r') as f:
				processed = json.load(f)
			processed.append({
				'email_id': str(email_id),
				'processed_at': datetime.datetime.now().isoformat()
			})
			with open(self.processed_emails_file, 'w') as f:
				json.dump(processed, f, indent=2)
		except:
			pass

	def process_email(self, email_id, email_bytes):
		"""Main processing pipeline"""
		result = {
			'email_id': str(email_id),
			'status': None,
			'job_id': None,
			'errors': [],
			'timestamp': datetime.datetime.now().isoformat()
		}
		
		email_data = self.parse_email_body(email_bytes)
		if not email_data:
			result['status'] = 'parse_error'
			return result
		
		sender_email = email_data['from']
		print(f"\n📧 Processing email from {sender_email}")
		print(f" Subject: {email_data['subject']}")
		
		# 3-LAYER EXTRACTION
		order_details = self.extract_order_details(email_data['body'])
		
		# VALIDATE
		is_valid, errors, suggestions = self.validate_order(order_details, sender_email)
		
		if is_valid:
			# CREATE ORDER
			order = self.create_order(order_details, sender_email)
			self.send_acknowledgment_email(order)
			result['status'] = 'success'
			result['job_id'] = order['job_id']
			self.mark_email_as_processed(email_id)
		else:
			# ESCALATE
			exception = self.log_exception(email_data, order_details, errors, suggestions, sender_email)
			self.send_exception_email(
				sender_email,
				order_details.get('customer_name'),
				errors,
				suggestions,
				email_data['subject']
			)
			result['status'] = 'validation_error'
			result['errors'] = errors
			self.mark_email_as_processed(email_id)
		
		return result

	def run(self, check_interval=30, process_limit=5):
		"""Main agent loop"""
		print("\n" + "="*60)
		print("🚀 Transportation Order Creation Agent V2")
		print("3-Layer: Regex → Gemini → Human")
		print("="*60)
		print(f"Email: {self.config['email']}")
		print(f"Check interval: {check_interval}s")
		print(f"Max emails per cycle: {process_limit}")
		print("="*60)
		print("\nAgent is running... Press Ctrl+C to stop\n")
		
		cycle = 0
		try:
			while True:
				cycle += 1
				print(f"\n[Cycle {cycle}] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
				
				mail = self.connect_imap()
				if not mail:
					print(f"⏳ Retrying in {check_interval}s...")
					time.sleep(check_interval)
					continue
				
				emails = self.fetch_unread_emails(mail, limit=process_limit)
				if not emails:
					print("✓ No unread emails")
				else:
					print(f"\n--- Processing {len(emails)} email(s) ---")
					for email_id, email_bytes in emails:
						result = self.process_email(email_id, email_bytes)
						if result['status'] == 'success':
							print(f" ✅ SUCCESS - Job: {result['job_id']}")
						elif result['status'] == 'validation_error':
							print(f" ⚠️ VALIDATION ERROR - Escalated to human review")
						else:
							print(f" ❌ ERROR - {result['status']}")
				
				mail.close()
				mail.logout()
				
				# Show Gemini stats
				try:
					with open(self.gemini_stats_file, 'r') as f:
						stats = json.load(f)
					print(f"\n📊 Gemini Stats: Total={stats['total_calls']}, Success={stats['successful']}, Failed={stats['failed']}")
				except:
					pass
				
				print(f"⏳ Next check in {check_interval}s...")
				time.sleep(check_interval)
		
		except KeyboardInterrupt:
			print("\n\n✋ Agent stopped by user")
			print("="*60)


def main():
	"""Entry point"""
	
	email_config = {
		'email': 'r.vikram176one@gmail.com',
		'password': 'kgqe luye gupx emvo',
		'imap_server': 'imap.gmail.com',
		'smtp_server': 'smtp.gmail.com',
		'imap_port': 993,
		'smtp_port': 587
	}
	
	if email_config['email'] == 'your_email@gmail.com':
		print("❌ ERROR: Configuration not updated!")
		return
	
	agent = TransportOrderAgent(email_config)
	agent.run(check_interval=30, process_limit=5)


if __name__ == '__main__':
	main()
