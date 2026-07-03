import logging
logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self):
        self.name = "example-metrics-reporter"

    async def on_workflow_finish(self, workflow_id: str, status: str, **kwargs):
        logger.info(f"Example plugin: Workflow {workflow_id} finished with status {status}")
        return {"workflow_id": workflow_id, "status": status, "reported": True}
