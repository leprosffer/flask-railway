# session_manager.py
def set_active_table(nom_table):
    with open("active_table.txt", "w") as f:
        f.write(nom_table)

def get_active_table():
    try:
        with open("active_table.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
