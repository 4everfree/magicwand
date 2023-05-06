import sys
import urllib.request
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import requests
import os

def read_m3u8_from_disk(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def parse_m3u8(url):
    video_urls = []
    content = read_m3u8_from_disk(sys.argv[1])
    content = content.splitlines()
    return [line.strip() for line in content if line.strip() and not line.startswith('#')]

def parse_m3u(url):
    video_urls = []
    with open(url, 'r') as f:
        lines = f.readlines()

    return [line.strip() for line in lines if line.strip() and not line.startswith('#')]

def download_file(url, filename):
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")


def concatenate_ts_files(directory, output_filename):
    natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]
    ts_files = sorted([f for f in os.listdir(directory) if f.endswith('.ts')], key=natsort)

    with open("file_list.txt", "w") as file:
        for filename in ts_files:
            file.write(f"file '{os.path.join(directory, filename)}'\n")

    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_filename])
    os.remove("file_list.txt")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Использование: python script.py <url> <количество потоков> <папка для загрузки>')
        sys.exit(1)

    m3u8_url = sys.argv[1]
    num_threads = int(sys.argv[2])
    download_path = sys.argv[3]
    video_urls = []

    if (not os.path.exists(download_path)):
        os.makedirs(download_path, exist_ok=True)
        if(m3u8_url.endswith('m3u8')):
            video_urls = parse_m3u8(m3u8_url)
        else:
            video_urls = parse_m3u(m3u8_url)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i, video_url in enumerate(video_urls):
                filename = os.path.join(download_path, f'00{i}.ts')
                executor.submit(download_file, video_url, filename)

    if len(video_urls) == len(os.listdir(download_path)):
        concatenate_ts_files("./result", "output.mp4")