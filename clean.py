import argparse
import helpers
import logging
import os
import subprocess
import sys

from prompter import yesno

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

regions = ["us-west-2", "us-east-1"]

parser = argparse.ArgumentParser()
parser.add_argument("--production_account_id")
parser.add_argument("--security_account_id")
parser.add_argument(
    "--assume_role",
    help="Must be a consistently assumed role name for all accounts.",
    default="OrganizationAccountAccessRole",
)
parser.add_argument(
    "--dry_run",
    help="Pre-flight test to run prior to destructive commits.",
    action="store_true",
)
parser.parse_args()
args = parser.parse_args()

if args.dry_run:
    logger.info("Running in dry-run mode. No destructive actions will be taken.")

yesno(
    "This will delete all resources in your accounts except for IAM users and roles. \
Please confirm that you would like to delete ALL resources in the production, security \
and root accounts."
)

logging.info("Proceeding with deletion of resources.")
logging.info("Cleaning up CloudFormation stack sets in the root account.")

for _ in regions:
    session = helpers.get_session(region_name=_)
    stack_sets = helpers.get_stack_sets(session)
    delete_nested = helpers.delete_nested(session, stack_sets, dry_run=args.dry_run)

logging.info("Nested Stacks Cleaned Up")
accounts = [args.production_account_id, args.security_account_id]
cleanup_routines = [
    "delete-cloudformation-stacks",
    "delete-cloudwatch-logs",
    "delete-lambdas",
    "delete-s3-buckets",
    "delete-ec2",
]
accounts.append(helpers.this_account(session))

for id in accounts:
    for _ in regions:
        session = helpers.get_session(region_name=_)
        logger.info(f"Cleaning up account={id} in region={_} using Custodian.")
        if id != helpers.this_account(session):
            credentials = helpers.assume_org_admin(session, id, role_name=args.assume_role)
            logger.info(f"Successfully assumed role for {id} in region={_}")

            aki = credentials["Credentials"]["AccessKeyId"]
            ask = credentials["Credentials"]["SecretAccessKey"]
            ast = credentials["Credentials"]["SessionToken"]
        for routine in cleanup_routines:
            logger.info(f"Running cleanup_routine={routine} in account_id={id}")
            environ = os.environ.copy()

            if id != helpers.this_account(session):
                environ["AWS_ACCESS_KEY_ID"] = f"{aki}"
                environ["AWS_SECRET_ACCESS_KEY"] = f"{ask}"
                environ["AWS_SESSION_TOKEN"] = f"{ast}"
            else:
                logger.info("Cleanup is being performed on the root account.")
            cmd = ["custodian", "run", "--dry-run", "-s", "output", f"{routine}.yml"]
            if args.dry_run == False:
                cmd.pop(2)
            subprocess.run(cmd, stdout=subprocess.PIPE, env=environ)
