import gradio as gr
import polars as pl
import os


def read_leaderboard() -> pl.DataFrame:
    return (
        pl.read_parquet(
            os.path.join("data", "mean_sequence+_combo_leaderboard.parquet")
        )
        .filter(pl.col("combo").str.split("-").list.get(0) !=
                pl.col("combo").str.split("-").list.get(1))
    )

leaderboard_df = read_leaderboard()

player_names = leaderboard_df["player_name"].unique().to_list()

combos = leaderboard_df["combo"].unique().to_list()

def filter_leaderboard(name: str, combo: str) -> pl.DataFrame:
    return leaderboard_df.filter(
        pl.col("player_name") == name,
        pl.col("combo") == combo
        if combo else pl.lit(True)
    )


if __name__ == "__main__":
    with gr.Blocks() as interface:
        gr.Markdown("# 2024 Sequence+ Dashboard")
    
        with gr.Tab(label="Player Search"):
            with gr.Row():

                with gr.Column():
                    with gr.Row():
                        metrics_df = gr.DataFrame(
                            label="Sequence+ by Pitch Combo",
                        )
                    
                    with gr.Row():
                        gr.DownloadButton(
                            label="Download",
                            value=os.path.join("data", "sequence+.csv"),
                        )

                with gr.Column():
                    with gr.Group():
                        player_name = gr.Dropdown(
                            label="Player Name",
                            choices=[None] + player_names,
                            interactive=True,
                        )
                        combo = gr.Dropdown(
                            label="Pitch Combo",
                            choices=[None] + combos,
                            interactive=True,
                        )

                    player_search_button = gr.Button("Go")
                    player_search_button.click(
                        fn=filter_leaderboard,
                        inputs=[player_name, combo],
                        outputs=metrics_df,
                    )


            with gr.Row():
                gr.Markdown("# Vizualizations")

            with gr.Group():
                with gr.Row():
                    with gr.Column():
                        gr.Plot(label="Sequence+ Distribution by Pitch Combo")
                    
                    with gr.Column():
                        gr.Plot(label="Rolling Sequence+")
                
                with gr.Row():
                    with gr.Column():
                        gr.Plot(label="Best Sequence+ 3D Trajectory")
                    
                    with gr.Column():
                        gr.Plot(label="Sequence+ by location by most popular pitch type")
            
            with gr.Row():
                gr.Markdown("# Video")
                
            with gr.Group():
                with gr.Row():
                    with gr.Column():
                        prev_vid = gr.PlayableVideo(label="First Pitch")
                    with gr.Column():
                        pitch_vid = gr.PlayableVideo(label="Second Pitch")
                with gr.Row():
                    random_seq_btn = gr.Button("Get Random Sequence Video")


    interface.launch(show_error=True, debug=True)
