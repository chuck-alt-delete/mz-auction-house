from dotenv import dotenv_values

# Load values from .env file into config dictionary.
# See example.env for what variables you need to define.
config = dotenv_values()

# Set Materialize cluster name
CLUSTER = "auction_house"

# Create Data Source Name (DSN) string
DSN = f'user={config["MZ_USER"]} password={config["MZ_PASSWORD"]} host={config["MZ_HOST"]} port={config["MZ_PORT"]} dbname={config["MZ_DB"]} sslmode=require'

if __name__=="__main__":
    print(config)
    print(DSN)