from dotenv import dotenv_values
from pathlib import Path

path_to_env = Path(__file__).parent.absolute() / ".env"

# Load values from .env file into config dictionary.
config = dotenv_values(path_to_env)

config["options"] = ''
if config["MZ_CLUSTER"]:
    config["options"] += f'--cluster={config["MZ_CLUSTER"]}'
else:
    config["options"] += '--cluster=quickstart'

if config["MZ_TRANSACTION_ISOLATION"]:
    config["options"] += f' -c transaction_isolation={config["MZ_TRANSACTION_ISOLATION"]}'

if config["MZ_SCHEMA"]:
    config["options"] += f' -c search_path={config["MZ_SCHEMA"]}'
    
DSN = f'''postgresql://{config["MZ_USER"]}:{config["MZ_PASSWORD"]}@{config["MZ_HOST"]}:{config["MZ_PORT"]}/{config["MZ_DB"]}?options=--cluster%3D{config["MZ_CLUSTER"]}%20-csearch_path%3D{config["MZ_SCHEMA"]}'''

if __name__=="__main__":
    print(config)