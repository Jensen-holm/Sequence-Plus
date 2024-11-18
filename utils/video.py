from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Any, Union
from bs4 import BeautifulSoup, Tag
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


def get_savant_video(plays: pl.DataFrame) -> None:
    game_infos = {
        game_pk: _get_game_info(game_pk=game_pk)
        for game_pk in plays["game_pk"].unique().to_list()
    }

    play_df = pl.concat([
        _get_play_data(game_info=game_info, game_pk=game_pk)
        for game_pk, game_info in game_infos.items()
    ], how="diagonal_relaxed")

    play_df = play_df.join(
        other=plays.with_columns(
            pl.col("inning").cast(pl.Int64),
        ),
        left_on=["ab_number", "inning", "game_pk", "pitch_number"],
        right_on=["at_bat_number", "inning", "game_pk", "pitch_number"],
        how="inner",
    )
    
    assert len(play_df["play_id"]) > 0

    cpus = os.cpu_count()
    assert cpus is not None
    
    url_max_workers = min(16, len(play_df["play_id"]), cpus * 4)
    pbar = tqdm(total=len(play_df["play_id"]) * 2)
    with ThreadPoolExecutor(max_workers=url_max_workers) as executor:
        video_urls = [
            executor.submit(_get_video_src, play_id)
            for play_id in play_df["play_id"]
        ]

        results = []
        for future in as_completed(video_urls):
            video_src = future.result()
            results.append(video_src)
            pbar.update(1)
        
        play_df = play_df.with_columns(
            pl.Series(
                name="video_url",
                values=results,
            )
        )

    play_df = play_df.drop_nulls(subset="video_url")
    if play_df .is_empty():
        return
    
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    video_max_workers = min(16, len(play_df["video_url"]), cpus * 4)
    with ThreadPoolExecutor(max_workers=video_max_workers) as executor:
        # pids = [executor.submit(_download_video, v, f"{i}.mp4")
        #         for i, v in enumerate(play_df["video_url"])]
        pids = [
            executor.submit(_download_video, v, f"{game_pk}_{play_id}.mp4")
            for v, game_pk, play_id in zip(play_df["video_url"], play_df["game_pk"], play_df["play_id"])
        ]
        for future in as_completed(pids):
            future.result()
            pbar.update(1)


def _download_video(video_url: str, save_path: str, _max_retries: int = 5, _wait_time: float = 1.0) -> None:
    if _max_retries <= 0:
        return None
    if not video_url or video_url is None:
        return None

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
) -> Optional[str]:
    if _max_retries <= 0:
        return None

    video_url = _BASE_VIDEO_URL.format(play_id=play_id)
    try:
        resp = requests.get(video_url)
        assert resp.status_code == 200, f"bad response code: {resp.status_code}"

        soup = BeautifulSoup(resp.content, "html.parser")
        video_container = soup.find("div", attrs={"class": "video-box"})
        if not isinstance(video_container, Tag):
            raise ValueError("Video container not found")

        video = video_container.find("video")
        assert isinstance(video, Tag)

        source = video.find("source", attrs={"type": "video/mp4"})
        assert isinstance(source, Tag)

        video_src = source.get("src")
        assert video_src
            
        # Handle the case where video_src could be a string or list of strings
        if isinstance(video_src, list):
            return video_src[0] if video_src else None
        return video_src if video_src != "" else None
    except Exception as e:
        print(f"Error: '{e}' \nOccoured when requesting game data from '{video_url}'")
        time.sleep(_wait_time)
        return _get_video_src(
            play_id=play_id, _max_retries=_max_retries-1, _wait_time=_wait_time
        )


def _get_play_data(game_info: dict, game_pk: int) -> pl.DataFrame:
    away_batters = game_info.get("away_batters", None)
    assert away_batters is not None, f"Away Batter data unavailable for '{game_pk}'"
    home_batters = game_info.get("home_batters", None)
    assert away_batters is not None, f"Home Batter data unavailable for '{game_pk}'"

    batters = away_batters | home_batters
    return pl.concat([
        pl.json_normalize(play, strict=False)
        for player in batters.values()
        for play in player
    ], how="diagonal_relaxed").with_columns(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("inning").cast(pl.Int64),
    )


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
        return _get_game_info(
            game_pk=game_pk, _max_retries=_max_retries - 1, _wait_time=_wait_time
        )


if __name__ == "__main__":
    # last and second to last pitches of 2024 WS
    play_df = pl.from_dict({
        "game_pk": [775296, 775296],
        "inning": [9, 9],
        "at_bat_number": [89, 89],
        "pitch_number": [4, 3],
    })

    _ = get_savant_video(plays=play_df)
