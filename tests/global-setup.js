const { execSync } = require("child_process");
const path = require("path");

const PROJECT_ROOT = path.resolve(__dirname, "..");

module.exports = async function globalSetup() {
  execSync(
    `docker compose exec -T web python manage.py shell -c "
import datetime
from django.contrib.auth.models import User
from masters.models import Party
from production.models import Challan, ProcessReport, InspectionReport
from finance.models import Invoice, Payment, OpeningBalance

# Superuser for all tests
User.objects.filter(username='pw_testuser').delete()
su = User.objects.create_superuser('pw_testuser', 'pwtest@erp.local', 'pw_testpass')

# Test party
party, _ = Party.objects.update_or_create(name='PW Test Party', defaults={'is_active': True})

# Finance records so ledger, outstanding and API endpoints have data
OpeningBalance.objects.filter(party=party, remarks='pw_setup').delete()
OpeningBalance.objects.create(party=party, effective_date=datetime.date(2024, 1, 1), balance_type='debit', amount=1000, remarks='pw_setup')

Invoice.objects.filter(party=party, invoice_number='PW-INV-001').delete()
inv = Invoice.objects.create(party=party, invoice_number='PW-INV-001', invoice_date=datetime.date(2024, 2, 1), amount=5000)

Payment.objects.filter(party=party, reference_number='PW-PAY-001').delete()
Payment.objects.create(party=party, payment_date=datetime.date(2024, 3, 1), amount=2000, mode='neft', reference_number='PW-PAY-001')

# Challan so production API and receipt PDF have data
Challan.objects.filter(party=party, challan_number='PW-CH-001').delete()
challan = Challan.objects.create(party=party, challan_number='PW-CH-001', challan_date=datetime.date(2024, 4, 1), direction='OUT', weight_kg=10, amount=500, job_description='Test Job')

# ProcessReport for admin bulk-action tests (no pdf required — field is nullable)
ProcessReport.objects.filter(party=party, ref_no='PW-SETUP-REF').delete()
ProcessReport.objects.create(party=party, ref_no='PW-SETUP-REF', part_name='Setup Test Part', generated_by=su)

print('global setup complete — user, party, finance records, challan, process report created')
"`,
    { cwd: PROJECT_ROOT, stdio: "inherit" }
  );
};
