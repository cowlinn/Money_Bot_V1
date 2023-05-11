# rough idea for clustering model
# make a model based on time-clustering of peaks of higher order derivative percentage changes 
        # need to somehow identify clusters, whether we are in a cluster and what the next move of the cluster will be
        # the absolute values might be useful here
        # maybe have some threshold value for absolute seventh order derivative and say that if abs is above that, its in a cluster, then spaces where it drops below threshold are between clusters?
        # study higher order derivatives (maybe 3rd onwards)
# The goal of building this model is to identify ways we can characterise the fractals which make up financial data
# if we are able to generate real-looking data with certain identified characterisitcs, we can measure those same characteristics in real data
# this allows us to build a sound statistical model of price movement