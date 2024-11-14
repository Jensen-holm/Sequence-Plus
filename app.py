import statcast_pitches
import gradio as gr
import polars as pl
import joblib
import os
from pipeline.v1.pipe import * 


def load_data(start_dt, end_dt) -> pl.DataFrame:
    run_values_lf = pl.scan_csv(
        os.path.join("data", "run_values.csv")
    )

    return (statcast_pitches.load()
            .filter(pl.col("game_date").dt.date() >= start_dt
                    & pl.col("game_date").dt.date() <= end_dt)
            .pipe(add_pitch_run_value, run_values_lf)
            .pipe(mirror_lhp_to_rhp)
            .pipe(convert_release_y_to_ft)
            .pipe(estimate_time_to_50ft)
            .collect())


if __name__ == "__main__":
    MODEL = joblib.load(
        os.path.join("models", "Sequence+1.0.joblib")
    ) 

    with gr.Blocks() as interface:
        gr.Markdown("# Sequence+ Dashboard")

        with gr.Row():
            with gr.Column():
                start_date = gr.DateTime(
                    label="Start Date",
                    value="2024-01-01",
                    type="datetime",
                    include_time=False
                )
            with gr.Column():
                end_date = gr.DateTime(
                    label="End Date",
                    value="2024-12-31",
                    type="datetime",
                    include_time=False
                )
        
        with gr.Row():
            with gr.Column():
                player = gr.Dropdown(
                    choices=load_data(start_date, end_date)["player_name"].to_list(),
                    label="Player Search",
                )

        with gr.Row():
            metrics_df = gr.DataFrame(
                label="Player Metrics",
            )
        
        with gr.Row():
            with gr.Column():
                plot = gr.Plot()
            
            with gr.Column():
                video_overlay = gr.Video()

    interface.launch(show_error=True, debug=True)
