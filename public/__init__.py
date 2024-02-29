import os


def get_path(path: str) -> str:
    ref_path = os.path.join(os.getcwd(), "public", path)
    if not os.path.exists(ref_path):
        os.mkdir(ref_path)

    return ref_path


VIDEO_PATH = get_path("videos")
AUDIO_PATH = get_path("audio")


if __name__ == "__main__":
    print(VIDEO_PATH)
    print(AUDIO_PATH)
