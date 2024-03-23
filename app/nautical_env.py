import os

class NauticalEnv:
    def __init__(self) -> None:
        self.SKIP_CONTAINERS = os.environ.get('SKIP_CONTAINERS', '')
        self.SKIP_STOPPING = os.environ.get('SKIP_STOPPING', '')
        self.SELF_CONTAINER_ID = os.environ.get('SELF_CONTAINER_ID', '')
        
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", 'INFO')
        self.REPORT_FILE_LOG_LEVEL = os.environ.get("REPORT_FILE_LOG_LEVEL", '')
        self.REPORT_FILE_ON_BACKUP_ONLY = os.environ.get("REPORT_FILE_ON_BACKUP_ONLY", '')

        self.DEST_LOCATION = os.environ.get("DEST_LOCATION", "")
        self.SOURCE_LOCATION = os.environ.get("SOURCE_LOCATION", "")
        
        
        self.REQUIRE_LABEL = False
        if os.environ.get("REQUIRE_LABEL", "False").lower() == True:
            self.REQUIRE_LABEL = True 