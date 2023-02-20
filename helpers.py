import boto3
import logging
import time

logger = logging.getLogger(__name__)


def get_session(region_name):
    return boto3.session.Session(region_name=region_name)


def get_root_ou_id(session):
    client = session.client("organizations")
    return client.list_roots()["Roots"][0]["Id"]


def get_stack_sets(session):
    client = session.client("cloudformation")
    return client.list_stack_sets()


def delete_nested(session, stack_set_list, dry_run=False):
    client = session.client("cloudformation")
    results = []
    for _ in stack_set_list["Summaries"]:
        stack_set_name = _["StackSetName"]
        if _["Status"] == "ACTIVE":
            delete_stack_instances(session, stack_set_name, dry_run)
            if dry_run == True:
                logger.info("Skipping actual deletion for dry-run.")
            else:
                result = client.delete_stack_set(StackSetName=stack_set_name)
                results.append(results)
            logger.info(
                f"Attempting deletion of stack set stack_set_name={stack_set_name}."
            )
        else:
            logger.info(
                f"Stack stack_set_name={stack_set_name} is inactive. No maintenance required."
            )
    logger.info(f"Stack set cleanup complete. results={results}")


def get_stack_ous(session, stack_set_name):
    ous = []
    client = session.client("cloudformation")
    stack_instances = client.list_stack_instances(StackSetName=stack_set_name)
    for _ in stack_instances["Summaries"]:
        result = client.describe_stack_instance(
            StackSetName=stack_set_name,
            StackInstanceAccount=_["Account"],
            StackInstanceRegion=_["Region"],
        )
        ous.append(result["StackInstance"]["OrganizationalUnitId"])
    return list(dict.fromkeys(ous))


def delete_stack_instances(session, stack_set_name, dry_run=False):
    client = session.client("cloudformation")
    response = client.list_stack_instances(StackSetName=stack_set_name)
    if len(response["Summaries"]) > 0:
        for _ in response:
            if dry_run == False:
                result = client.delete_stack_instances(
                    StackSetName=stack_set_name,
                    Regions=["us-west-2", "us-east-1"],
                    RetainStacks=False,
                    DeploymentTargets={
                        "OrganizationalUnitIds": get_stack_ous(session, stack_set_name)
                    },
                )
                logger.info(f"Operation in progress: result={result}")
                logger.info("Waiting 60 seconds between deletions.")
                time.sleep(60)

                try:
                    result = client.list_stack_instances(StackSetName=stack_set_name)
                    while result["Summaries"]["0"] == "PENDING":
                        time.sleep(3)
                        logger.info(f"Deletion of {stack_set_name} is pending.")
                        result = client.list_stack_instances(
                            StackSetName=stack_set_name
                        )
                except Exception as e:
                    logger.error(
                        f"Could not query for {stack_set_name} due to {e}. It is probably deleted."
                    )
            else:
                logger.info(f"Skipping deletion of {stack_set_name} due to dry run.")


def assume_org_admin(session, account_id, role_name):
    client = session.client("sts")
    response = response = client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
        RoleSessionName="course.cleanup",
        DurationSeconds=3600,
    )
    return response


def this_account(session):
    client = session.client("sts")
    return client.get_caller_identity()["Account"]
