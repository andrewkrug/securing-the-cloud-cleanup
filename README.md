# Securing the Cloud Cleanup

So, you've finished Securing the Cloud Foundations and now you're ready to say goodbye to that pesky AWS Bill.
This CLI that wraps cloud-custodian will help clean out all the nooks and crannies in your account to makes sure
that you pay as little as possible.

## Assumptions

1. You did not deploy any resources in regions besides us-east-1 and us-west-2.
2. You did not activate any services that weren't covered in the class.
3. You consistently named and tagged any Cloudformation you were asked to.
4. You have note deleted OrganizationAccountAccessRole

## Before running this

1. Sign into your Organization root account and "Update stack" on the first user stack you created and the UnfederatedRoles (Note: these may have different names in your account).  In the update stack wizard add the following tag `long-running:true` to the stack.  This will ensure that custodian doesn't destroy your ability to log in.
2. Assume the UnfederatedAdministrator in your shell.
3. Inside of this project create a virtualenv `virtualenv venv -p python3` should do the job if you're using the virtual machine provided for the course.
4. `source venv/bin/activate && pip3 install -r requirements.txt` to install the dependencies.
5. Get the account ids for your production and security account from the AWS Organizations console.  Note: They are also in your `~/.aws/config`
6. Ensure you have detached any **restrictive SCPs** that could potentially prevent the tools from running.
7. Run the script by typing `python3 clean.py --production_account_id 123456 --security_account_id 123456`

> Note: The script has a `--dry_run`ss flag if you simply want to see it go through the motions.

This will run a cleanup for you beginning in the production account, followed by the security account, and finally the root account.
It will leave your UnfederatedUsers in place _they don't cost any money_.

## If you run into errors 

Some of the code that deletes the "StackSets" can run into conditions where it will error out. Should you encounter this simply run the script again.
Otherwise please file a github issue with the error output of the script and it will be triaged and addressed.

## After running this 

Keep an eye on your AWS Bill for a few days.  It should be near zero or pennies per month to simply keep the lab around.
Alternatively you can follow the [account closure process]('https://aws.amazon.com/premiumsupport/knowledge-center/close-aws-account/'). You will need to do this
for every subordinate account in your organization INDIVIDUALLY by first resetting the root password using the e-mail you created for that.