from django.db import migrations

SQL = """
UPDATE traffic_control_blockedrequest
   SET user_id = NULLIF(request_data->>'user_id', '')::int,
       block_reason = request_data->>'block_reason'
 WHERE user_id IS NULL
"""

REVERSE_SQL = """
UPDATE traffic_control_blockedrequest
   SET user_id = NULL,
       block_reason = NULL
"""


class Migration(migrations.Migration):
    dependencies = [
        ("traffic_control", "0008_blockedrequest_block_reason_blockedrequest_user"),
    ]
    operations = [migrations.RunSQL(SQL, reverse_sql=REVERSE_SQL)]
