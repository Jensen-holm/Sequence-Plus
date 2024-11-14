from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any
from bs4 import BeautifulSoup
from tqdm import tqdm
import polars as pl
import requests
import time
import os


__all__ = ["get_savant_video"]


_BASE_VIDEO_URL = "https://baseballsavant.mlb.com/sporty-videos?playId={play_id}"

_BASE_GAME_URL = "https://baseballsavant.mlb.com/gf?game_pk={game_pk}"

VIDEO_DIR = os.path.join(
    os.path.sep.join(os.path.dirname(__file__).split(os.path.sep)[:-1]),
    "videos",
) 


def get_savant_video(game_pk: int, sv_ids: Optional[list[str]] = None) -> None:
    game_info = _get_game_info(game_pk=game_pk)
    assert isinstance(game_info, dict)

    play_id_df = _get_play_ids(game_info=game_info, game_pk=game_pk)
    if sv_ids is not None:
        play_id_df = (play_id_df
                      .filter(pl.col("sv_id").is_in(sv_ids)))
    
    cpus = os.cpu_count()
    assert cpus is not None
    
    url_max_workers = min(16, len(play_id_df["play_id"]), cpus * 4)
    pbar = tqdm(total=len(play_id_df["play_id"]) * 2)
    with ThreadPoolExecutor(max_workers=url_max_workers) as executor:
        video_urls = [
            executor.submit(_get_video_src, play_id)
            for play_id in play_id_df["play_id"]
        ]

        results = []
        for future in as_completed(video_urls):
            video_src = future.result()
            results.append(video_src)
            pbar.update(1)
        
        play_id_df = play_id_df.with_columns(
            pl.Series(
                name="video_url",
                values=results,
            )
        )

    play_id_df = play_id_df.drop_nulls(subset="video_url")
    if play_id_df.is_empty():
        return

    video_max_workers = min(16, len(play_id_df["video_url"]), cpus * 4)
    with ThreadPoolExecutor(max_workers=video_max_workers) as executor:
        pids = [executor.submit(_download_video, v, f"{game_pk}_{i}.mp4")
                for i, v in enumerate(play_id_df["video_url"])]
        for future in as_completed(pids):
            future.result()
            pbar.update(1)
    
    pbar.close()


def _download_video(video_url: str, save_path: str, _max_retries: int = 5, _wait_time: float = 1.0) -> None:
    if _max_retries <= 0:
        return None
    if not video_url or video_url is None:
        return None
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    try:
        with requests.get(video_url, stream=True) as r:
            with open(os.path.join(VIDEO_DIR, save_path), "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except Exception as e:
        print(f"Error: '{e}' \nOccoured when downloading video from '{video_url}'")
        time.sleep(_wait_time)
        _download_video(video_url=video_url, save_path=save_path, _max_retries=_max_retries-1)


def _get_video_src(
    play_id, _max_retries: int = 5, _wait_time: float = 1.0
) -> Optional[Any]:
    if _max_retries <= 0:
        return None

    video_url = _BASE_VIDEO_URL.format(play_id=play_id)
    try:
        resp = requests.get(video_url)
        assert resp.status_code == 200, f"bad response code: {resp.status_code}"

        soup = BeautifulSoup(resp.content, "html.parser")
        video_container = soup.find("div", attrs={"class": "video-box"})
        assert (
            video_container is not None
        ), f"div w/ class=video-box not found in video container soup"

        video = video_container.find("video")
        assert (
            video is not None
        ), f"video attribute unable to be located in video container soup"

        src = video.find("source", type="video/mp4")
        assert src is not None, f"video source could not be found in video soup"

        video_src = src.get("src", None)
        assert video_src is not None, f"video src could not be found"
        return video_src if video_src != "" else None
    except Exception as e:
        print(f"Error: '{e}' \nOccoured when requesting game data from '{video_url}'")
        time.sleep(_wait_time)
        _get_video_src(
            play_id=play_id, _max_retries=_max_retries-1, _wait_time=_wait_time
        )


def _get_play_ids(game_info: dict, game_pk: int) -> pl.DataFrame:
    batters = game_info.get("away_batters", None)
    assert batters is not None, f"Batter data unavailable for '{game_pk}'"
    return pl.concat([
        pl.from_dict({
            "sv_id": play.get("sv_id", None),
            "play_id": play.get("play_id", None),
        })
        for player in batters.values()
        for play in player
    ])


def _get_game_info(
    game_pk: int, _max_retries: int = 5, _wait_time: float = 1.0
) -> Optional[Any]:
    if _max_retries <= 0:
        return None

    game_url = _BASE_GAME_URL.format(game_pk=game_pk)
    try:
        resp = requests.get(game_url)
        assert resp.status_code == 200, f"bad response code: {resp.status_code}"
        data = resp.json()
        assert data is not None, f"Data is None"
        return data
    except Exception as e:
        print(f"Error: '{e}' \nOccoured when requesting game data from '{game_url}'")
        time.sleep(_wait_time)
        _get_game_info(
            game_pk=game_pk, _max_retries=_max_retries - 1, _wait_time=_wait_time
        )


if __name__ == "__main__":
    _ = get_savant_video(775302)
