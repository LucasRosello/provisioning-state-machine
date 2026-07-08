"""WaitForApproval: task-token callback approval gate.

Invoked via the .waitForTaskToken pattern. The task token is persisted on the
request row so an external approver (portal/API) can resume the execution with
SendTaskSuccess / SendTaskFailure.

Demo mode (AUTO_APPROVE=true) resolves immediately by calling SendTaskSuccess so
the flow can be exercised without a human in the loop.
"""
import os

import platform_common as pc

AUTO_APPROVE = os.environ.get("AUTO_APPROVE", "false").lower() == "true"


def handler(event, _context):
    request_id = event["request_id"]
    task_token = event["task_token"]
    approval = event.get("approval", {})

    pc.update_request_status(request_id, "WAITING_APPROVAL", {"approval_task_token": task_token})
    pc.audit(request_id, "APPROVAL_REQUIRED", approval)

    if AUTO_APPROVE:
        pc.audit(request_id, "APPROVAL_APPROVED", {"mode": "auto-approve-demo"})
        pc.send_task_success(task_token, {"approved": True, "approver": "auto-approve-demo"})

    # In non-demo mode we return nothing and stay paused until the external
    # approver calls SendTaskSuccess/SendTaskFailure with this token.
    return {}
