import base64
import os

class DB:
    def __init__(self, db_path):
        self.db_path = db_path

    def base64_encode(self, data):
        return base64.b64encode(data.encode()).decode()

    def base64_decode(self, data):
        return base64.b64decode(data.encode()).decode()

    def get(self, key):
        with open(self.db_path, 'r') as f:
            encoded_key = self.base64_encode(key)
            for line in f:
                if line.startswith(encoded_key + " "):
                    _, encoded_value = line.strip().split(" ", 1)
                    return self.base64_decode(encoded_value)
        return None

    def list(self):
        with open(self.db_path, 'r') as f:
            return [self.base64_decode(line.split(" ", 1)[0]) for line in f]

    def last(self):
        with open(self.db_path, 'r') as f:
            lines = f.readlines()
            if lines:
                _, encoded_value = lines[-1].strip().split(" ", 1)
                return self.base64_decode(encoded_value)
        return None

    def put(self, key, value):
        encoded_key = self.base64_encode(key)
        encoded_value = self.base64_encode(value)

        found = False
        lines = []
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                lines = f.readlines()

        with open(self.db_path, 'w') as f:
            for line in lines:
                if line.startswith(encoded_key + " "):
                    f.write(f"{encoded_key} {encoded_value}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"{encoded_key} {encoded_value}\n")

    def delete(self, key):
        encoded_key = self.base64_encode(key)
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                lines = f.readlines()
            with open(self.db_path, 'w') as f:
                for line in lines:
                    if not line.startswith(encoded_key + " "):
                        f.write(line)
