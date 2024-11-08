# Sequence+

The main goal of Sequence+ is to create a model like [Stuff+](), [Location+](), and [Pitcher+]() that aims to measure the run value of a pitch sequence. Sequence+ will be made using features related to tunneling, and a mix of things that are typically included in [Location+]() and [Stuff+]().

# Tunneling

Earlier this year I created [Tunnel Score]() to try and quantify how well any given two pitch sequence was tunneled. Overall it doesn't do a bad job, but it is hard to capture how 'good' a pitch was truly tunneled with just this one number. 

In addition Tunnel Score only considers the difference between 2D locations of the ball when they cross the plate, and where they would have crossed the plate without induced movement. This could be improved by considering the 3D distance between pitches in a two pitch sequence at [decision time]() (~0.12 seconds) and [commit time]() (~0.167 seconds) into the balls flight path. 

# 3D pitch displacement calculation

## Step 1: Time to 50ft. from home plate

Estimate the time it took the baseball to travel from release point to 50ft from home plate (the point where we have measurements for a &v in x, y, z dimensions)

```math
t_{50} = \frac{(60 + 6/12) - 50 - extension}{vft * 1.05}
```

Where ...

extension = distance from the rubber where the pitch was released

vft = release_speed in ft/s

I multiply the velocity by 1.05 in order to dialate the time by 5%. This makes our estimation of position more accurate because it helps account for error that we get from assuming that acceleration is constant in the kinematic equations for displacement.

**New Features**
- `t50`: estimated time it took the ball to get to 50ft. from home plate
- `release_pos_y`: release position in the y dimension converted to feet

## Step 2: x, y, & z positions at 50ft. from home plate

For this I use the kinematic equations with the acceleration, velocity and now our time estimate, $t_{50}$, to calculate displacement in each dimension.

```math
d_{50} = r_{dim} + v_{dim} * t_{50} * \frac{1}{2} * a_{dim} * t_{50}^2
```

Where ...

rdim = release position in x, y or z dimension

vdim = velocity at 50ft. from home plate in x, y or z dimension

adim = acceleration at 50ft. from home plate in x, y or z dimension

t50 = estimated time that it took to get to 50ft. from home plate from step 1

**New Features**
- `x50`: position in the x dimension when the ball is 50ft. from home plate
- `y50`: position in the y dimension when the ball is 50ft. from home plate
- `z50`: position in the z dimension when the ball is 50ft. from home plate

## Step 3: Estimate 3D positions at commit time & decision time

Now we can make an estimate of where the ball is in all dimensions, at any given time. But I am interested specifically in 0.120 seconds after release (commit time), and 0.167 seconds after release (decision time).

For this I use the same formula that I used to esimate position at 50ft. from home plate, except I start from that 50ft. mark by calculating the difference in time between $t_{50}$ and $t_{i}$.

```math
d_{i} = p_{50} + v_{50} * (t_{50} - t_{i}) * \frac{1}{2} * a_{50} * (t_{50} - t_{i})^2
```

Where ...

p50 = position in x, y, or z dimension at 50 ft. from home plate

I am assuming that both $v$ and $a$ are constant, again using a 5% time dilation as a crutch to help account for this.

**New Features**
- `x_0.120`: position in the x dimension at 0.120 seconds after release (commit time)
- `y_0.120`: position in the y dimension at 0.120 seconds after release (commit time)
- `y_0.120`: position in the z dimension at 0.120 seconds after release (commit time)
- `x_0.167`: position in the x dimension at 0.120 seconds after release (decision time)
- `y_0.167`: position in the y dimension at 0.120 seconds after release (decision time)
- `y_0.167`: position in the z dimension at 0.120 seconds after release (decision time)
- `x_plate`: position in the x dimension when the ball crossed the plate
- `y_plate`: position in the y dimension when the ball crossed the plate
- `z_plate`: position in the z dimension when the ball crossed the plate

**Visualization & Accuracy** <br>
In order to make sure that this works, I created a plot of some randomly sampled pitches thrown by Yu Darvish this season.

- `Sweeper`: Purple
- `Splitter`: Yellow
- `Slider`: Green
- `Knuckle Curve`: Blue
- `Four Seam Fastball`: Red

![Sampled Darvish 3D pitch Shape Estimations](assets/darvish_samples.png)

I worked backwards from the 50ft. from home plate mark, and tried to estimate release position. Comparing this to actual release position will help me get an idea of how accurate / inaccurate this is.

![Position Estimation Accuracy](assets/ball_loc_accuracy_table.png)

# Road Map

- [x] Feature Engineering
- [ ] Feature Selection
- [ ] Model Building
- [ ] Evaluation
- [ ] Deploy in HuggingFace Dashboard

# References

[statcast-era-pitches]() <br>
Used this huggingface dataset to effeciently load dataset of pitches thrown from 2017-present.

[Carter Kessinger](https://x.com/ckessinger44) & [Johnny Davis](https://x.com/Johnny_Davis12)<br>
These guys sparked the idea for using kinematic equations for 3D distances at commit & decision points for a better [TunnelScore]().
