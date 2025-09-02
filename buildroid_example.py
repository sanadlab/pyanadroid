

import buildAnaDroid

source = "demoProjects/SampleApp"
#buildAnaDroid.extract_project_name(source)
buildAnaDroid.process_repository(repo_source=source, local_path=True)

# args:

# repo_source: str, num: int=40, conversation: bool=False, keep_container:bool=False, user_retry:bool=False, local_path:bool=False