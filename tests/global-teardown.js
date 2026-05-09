const { execSync } = require("child_process");
const path = require("path");

const PROJECT_ROOT = path.resolve(__dirname, "..");

module.exports = async function globalTeardown() {
  execSync(
    `docker compose exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import Party
from production.models import ProcessReport, InspectionReport
from finance.models import Invoice, Payment, OpeningBalance
from migration_app.models import MigrationBatch

# Remove imported batches created during tests (cascades to finance records they created)
MigrationBatch.objects.filter(source_file_name__startswith='pw_test').delete()

party_qs = Party.objects.filter(name='PW Test Party')
if party_qs.exists():
    party = party_qs.first()
    ProcessReport.objects.filter(party=party).delete()
    InspectionReport.objects.filter(party=party).delete()
    Invoice.objects.filter(party=party).delete()
    Payment.objects.filter(party=party).delete()
    OpeningBalance.objects.filter(party=party).delete()
    party.delete()

User.objects.filter(username='pw_testuser').delete()
print('global teardown complete')
"`,
    { cwd: PROJECT_ROOT, stdio: "inherit" }
  );
};
