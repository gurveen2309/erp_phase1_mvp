const { execSync } = require("child_process");
const path = require("path");

const PROJECT_ROOT = path.resolve(__dirname, "..");

module.exports = async function globalTeardown() {
  execSync(
    `docker compose exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import Party
from production.models import ProcessReport, InspectionReport
ProcessReport.objects.filter(party__name='PW Test Party').delete()
InspectionReport.objects.filter(party__name='PW Test Party').delete()
Party.objects.filter(name='PW Test Party').delete()
User.objects.filter(username='pw_testuser').delete()
print('test fixtures removed')
"`,
    { cwd: PROJECT_ROOT, stdio: "inherit" }
  );
};
