const { execSync } = require("child_process");
const path = require("path");

const PROJECT_ROOT = path.resolve(__dirname, "..");

module.exports = async function globalSetup() {
  execSync(
    `docker compose exec -T web python manage.py shell -c "
from django.contrib.auth.models import User
from masters.models import Party
User.objects.filter(username='pw_testuser').delete()
User.objects.create_superuser('pw_testuser', 'pwtest@erp.local', 'pw_testpass')
Party.objects.update_or_create(name='PW Test Party', defaults={'is_active': True})
print('test user + party created')
"`,
    { cwd: PROJECT_ROOT, stdio: "inherit" }
  );
};
