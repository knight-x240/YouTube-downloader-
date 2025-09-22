import requests

def upload_to_transfer_sh(file_path):
    # transfer.sh: simple and free for up to 10GB, 14 days retention
    with open(file_path, "rb") as f:
        response = requests.put(
            f"https://transfer.sh/{file_path}",
            data=f
        )
    if response.status_code == 200:
        return response.text.strip()
    else:
        raise Exception("Failed to upload to transfer.sh")