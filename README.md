# Sequence+

The main goal of Sequence+ is to create a model like [Stuff+](https://www.google.com/search?client=safari&rls=en&q=stuff%2B&ie=UTF-8&oe=UTF-8), [Location+](https://www.google.com/search?client=safari&rls=en&q=stuff%2B&ie=UTF-8&oe=UTF-8), and [Pitcher+](https://www.google.com/search?client=safari&rls=en&q=stuff%2B&ie=UTF-8&oe=UTF-8) that aims to measure the run value of a pitch sequence. Sequence+ will be made using features related to tunneling, and a mix of things that are typically included in Location+ & Stuff+.

# General Approach

I have a run expectancy matrix for 2024, that describes roughly how many runs each event in each possible situation is worth. Using this and pitch by pitch advanced data from the 2024 season, I am aiming to build a model that can predict the cumulative run expectancy for a given sequence of pitches. 

## Features

In order to try and include pitch tunneling in this model, I use the kinematic equations to estimate the location of the baseball in 3D space at the commit point, decision point, release, and over the plate.

![Yu Darvish Sample](./assets/darvish_samples.png)

See [3D_pitch_location_estimation.md](./DOCS/3D_pitch_location_estimation.md) or the feature engineering section of [sequence+.ipynb](./notebooks/sequence+.ipynb) for details on how I am doing this.

Some more features related to pitch sequences and pitch quality were added that would hopefully help explain variance in `delta_run_exp`.

## Feature Selection

Working on it ... the model I am building will be a black box, but I want to make it simple to provide input to this model. If I go with the LSTM model, I think this will probably look something like [embedded feature selection](https://arxiv.org/html/2312.17517v1#:~:text=One%20common%20approach%20for%20embedded,different%20time%20steps%20or%20features.)

## Model

I would like to predict cumulative `delta_run_exp` with a sequence of pitches of variable length. Models that are good at problems similar to this include ...

- [RNN](https://en.wikipedia.org/wiki/Recurrent_neural_network)
- [LSTM](https://en.wikipedia.org/wiki/Long_short-term_memory) (type of RNN) 

...

# Documentation

The jupyter notebooks in the [notebooks](./notebooks/) folder are in depth with lots of markdown going through my thouhgt process at each step. Also check out the content in the [DOCS](./DOCS/) directory for a more in depth look into how and why I did things. 

# Road Map

- [x] Feature Engineering
- [ ] Model Building
- [ ] Evaluation
- [ ] Deploy in HuggingFace Dashboard

# References

- [statcast-era-pitches](https://huggingface.co/datasets/Jensen-holm/statcast-era-pitches): Used this huggingface dataset to effeciently load dataset of pitches thrown from 2017-present.
- [Carter Kessinger](https://x.com/ckessinger44) & [Johnny Davis](https://x.com/Johnny_Davis12): These guys sparked the idea for using kinematic equations for 3D distances at commit & decision points for a better [TunnelScore]().
- [TJ Nestico](https://x.com/TJStats): He posts lots of great content on X, and I am using a pitch by pitch run expectancy matrix found in his project [tjStuff+](https://github.com/tnestico/tjstuff_plus)

# Contact

Feel free to reach out to me with any questions or feedback 

Email: jensenh87@gmail.com <br>
X: [@\_holmj\_](https://x.com/_holmj_)
