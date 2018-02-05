# SteamEra Games of the Year Awards 2017

## Goal

To rank the best games of the year, a Bayesian Rating is computed [on RPGCodex](http://www.rpgcodex.net/content.php?id=10819), which provides a solid ranking. However, this methodology is not applied [on SteamGAF/ERA](https://www.resetera.com/threads/steamera-games-of-the-year-awards-2017.19342/), and a sum of scores is applied instead (think Eurovision). Our goal is to use the data shown on SteamGAF/ERA and re-rank games with other methods:
* a Bayesian Rating,
* [Schulze method](https://en.wikipedia.org/wiki/Schulze_method).

## Bayesian Rating

### Prior for Bayesian Rating

Our prior is computed as follows:
* regarding the average score, the prior is the median of average scores,
* regarding the number of votes, the prior is the average of numbers of votes.

### Caveat

The original data consists in sets of GOTY candidates, which happen to be ranked. As pointed out by [Durante](https://www.resetera.com/posts/3904799/), interpreting the ranks as a score leads to undesirable properties.

## Schulze method

Schulze method is an alternative to Borda count. The code was copied from: https://github.com/woctezuma/schulze-method

### Data

The original dataset, which consists of the rankings submitted by each user, was used. It cannot be shared for privacy concerns.

## References

* https://fulmicoton.com/posts/bayesian_rating/

* https://en.wikipedia.org/wiki/Additive_smoothing

* https://planspace.org/2014/08/17/how-to-sort-by-average-rating/

* http://www.dcs.bbk.ac.uk/~dell/publications/dellzhang_ictir2011.pdf

