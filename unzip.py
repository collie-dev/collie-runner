import os
folder = "/Users/wph95/Downloads/diag-fNcG1DLDWm3.diag/monitor/metrics/172.31.40.244-9090"
to_folder = "/tmp/metric"

with open("unzip.bash", "w") as f:
    for count, filename in enumerate(os.listdir(folder)):
        # os.rename(f"{folder}/{filename}", f"{folder}/{filename}.zst")
        cmd = f"unzstd {folder}/{filename} -o {to_folder}/{filename[:-4]}\n"
        f.write(cmd)
