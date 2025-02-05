class Command(BaseCommand):
    help = "Download and process file from static URL - create csv vrsion of files"

    @classmethod
    def download_src():
        url = "https://aeronet.gsfc.nasa.gov/new_web/All_MAN_Data_V3.tar.gz"
        response = requests.get(url)

        if not response.ok:
            print("Server Offline. Attempt again Later.")
            return

        tar_contents = response.content

        with tarfile.open(fileobj=io.BytesIO(tar_contents), mode="r:gz") as tar:
            tar.extractall(path=r"./before_csv")
        print("MAN Data Downloaded ...")

        # Read the folder contents
        folder_path = os.path.join(".", "src")
        if os.path.exists(folder_path):
            print("Folder exist -> moving to creating threaded processes")
