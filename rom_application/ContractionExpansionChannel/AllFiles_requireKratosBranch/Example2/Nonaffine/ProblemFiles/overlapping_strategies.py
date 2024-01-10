import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans

def time_clustering(S, time_clusters = 3, overlaping_snapshots = 1 ):
    total_time_steps = S.shape[1]
    if time_clusters > total_time_steps:
        raise error
    sub_snapshots = np.array_split(S,time_clusters, axis=1)

    for i in range(time_clusters):
        if i == 0:
            correct_cluster = np.full((sub_snapshots[0].shape[1],), 0 )
        else:
            correct_cluster = np.r_[correct_cluster, np.full((sub_snapshots[i].shape[1],), i )]
        print(f'{i}\'th  sub-snapshot contains',(np.shape(sub_snapshots[i])[1]), 'columns before overlapping')

    #get list containing snapshots to add to each overlapped cluster
    if overlaping_snapshots is not 0:
        snapshots_to_add = {}
        for i in range(time_clusters):
            if i == 0:
                snapshots_to_add[0] = sub_snapshots[1][:,:overlaping_snapshots]
            elif i == time_clusters-1:
                snapshots_to_add[i] = sub_snapshots[i-1][:, -overlaping_snapshots:]
            else:
                snapshots_to_add[i] = sub_snapshots[i-1][:, -overlaping_snapshots:]
                snapshots_to_add[i] = np.c_[snapshots_to_add[i], sub_snapshots[i+1][:, :overlaping_snapshots] ]

        #actually enlarging sub_snapshots
        for j in range(time_clusters):
            sub_snapshots[j] = np.c_[sub_snapshots[j], snapshots_to_add[j]]
            print(f'{j}\'th  sub-snapshot contains',(np.shape(sub_snapshots[j])[1]), 'columns after overlapping')

    return sub_snapshots, correct_cluster


def ismember(A, B):
    if isinstance(A, np.int_):
        return [ np.sum(A == B) ]
    else:
        return [ np.sum(a == B) for a in A ]

def narrowing_clustering(S, narrowing, narrowing_clusters = 3, overlaping_snapshots = 1 ):
    kmeans = KMeans(n_clusters=narrowing_clusters, random_state=0).fit(narrowing.reshape(-1,1))
    #split snapshots into sub-sets
    sub_snapshots={}
    neighbors={}
    for i in range(narrowing_clusters):
        sub_snapshots[i] = S[:,kmeans.labels_==i]
        neighbors[i] = []
        correct_cluster = kmeans.labels_
        centroids = kmeans.cluster_centers_

    if narrowing_clusters>1:
        #try and use as is solution manifold neighbor identification
        #identify the two nearest cluster centroids to state i and mark these clusters as neighbors
        narrowing = narrowing.reshape(1,-1)
        for i in range(np.shape(narrowing)[1]):
            this_matrix = (kmeans.cluster_centers_).T - narrowing[:,i].reshape(np.shape(narrowing)[0], 1)
            distance = np.zeros((narrowing_clusters))
            for j in range(narrowing_clusters):
                distance[j] = np.linalg.norm(this_matrix[:,j])
            second_nearest_idx = np.argsort(distance)[1]
            if not(sum(ismember(neighbors[kmeans.labels_[i]],second_nearest_idx))):
                neighbors[kmeans.labels_[i]].append(second_nearest_idx)

        #get list containing snapshots to add to each overlapped cluster
        if True:
        #if overlaping_snapshots is not 0:

            snapshots_to_add = []
            for j in range(narrowing_clusters):
                N_neighbors = len(neighbors[j])
                N_add = overlaping_snapshots #number of snapshots to add to subset i (on each direction)

                for i in range(N_neighbors):
                    print('adding neighbors from ', neighbors[j][i], 'to cluster ', j  )
                    ith_narrowing_cluster = narrowing[:,kmeans.labels_==neighbors[j][i]]
                    this_matrix = ith_narrowing_cluster - ((kmeans.cluster_centers_[j]).T).reshape(np.shape(narrowing)[0], 1)
                    distance = np.linalg.norm(this_matrix, axis = 0)
                    #distance = np.zeros(np.shape(ith_narrowing_cluster[1]))
                    #for k in range(len(distance)):
                    #    distance[k] = np.linalg.norm(this_matrix[:,k])
                    indices_to_add = np.argsort(distance)
                    if i==0:
                        snapshots_to_add.append(sub_snapshots[neighbors[j][i]][:,indices_to_add[:N_add]])
                    else:
                        snapshots_to_add[j] =  np.c_[ snapshots_to_add[j] , sub_snapshots[neighbors[j][i]][:,indices_to_add[:N_add]] ]

            for j in range(narrowing_clusters):
                sub_snapshots[j] = np.c_[sub_snapshots[j], snapshots_to_add[j]]
                print(f'{j}\'th  sub-snapshot contains',(np.shape(sub_snapshots[j])[1]), 'columns after overlapping')


    return sub_snapshots, correct_cluster


def solution_manifold_clustering():
    pass



if __name__=='__main__':
    #S = np.load('SnapshotMatrix.npy')
    #narrowing = np.load('narrowing.npy')
    narrowing = np.linspace(0,1,12)
    S = np.array([[1,2,3,4,5,6,7,8,9,10,11,12],[1,2,3,4,5,6,7,8,9,10,11,12]])
    #a = narrowing.reshape(1,-1)
    #S = np.r_[a, a , a, a]
    sub_snapshots, correct_cluster = time_clustering(S, 3,0)
    #sub_snapshots, correct_cluster = narrowing_clustering(S, narrowing, 3, 2)
    #sub_snapshots, correct_cluster = solution_manifold_clustering(S)
    #sub_snapshots, correct_cluster = time_clustering(S)
    kkk = 5

    #


"""

def solution_manifold_clustering(S, solution_manifold_clusters = 3, overlaping_snapshots = 1 ):
    #S = np.load('SnapshotMatrix.npy')
    kmeans = KMeans(n_clusters = solution_manifold_clusters, random_state=0).fit(S.T)
    correct_cluster = kmeans.labels_

    #split snapshots into sub-sets
    sub_snapshots={}
    neighbors={}
    for i in range(solution_manifold_clusters):
        sub_snapshots[i] = S[:,kmeans.labels_==i]
        neighbors[i] = []
        print(f'{i}\'th  sub-snapshot contains',(np.shape(sub_snapshots[i])[1]), 'columns before overlapping')

    #identify the two nearest cluster centroids to state i and mark these clusters as neighbors
    for i in range(np.shape(S)[1]):
        this_matrix = (kmeans.cluster_centers_).T - S[:,i].reshape(np.shape(S)[0], 1)
        distance = np.zeros((solution_manifold_clusters))
        for j in range(solution_manifold_clusters):
            distance[j] = np.linalg.norm(this_matrix[:,j])
        second_nearest_idx = np.argsort(distance)[1]
        if not(sum(ismember(neighbors[kmeans.labels_[i]],second_nearest_idx))):
            neighbors[kmeans.labels_[i]].append(second_nearest_idx)

    snapshots_to_add = []

    for j in range(solution_manifold_clusters):
        N_snaps = np.shape(sub_snapshots[j])[1]
        N_neighbors = len(neighbors[j])

        N_add = overlaping_snapshots #number of snapshots to add to subset i (on each direction)
        for i in range(N_neighbors):
            print('adding neighbors from ', neighbors[j][i], 'to cluster ', j  )
            this_matrix = sub_snapshots[neighbors[j][i]] - ((kmeans.cluster_centers_[j]).T).reshape(np.shape(S)[0], 1)
            distance = np.zeros(np.shape(sub_snapshots[neighbors[j][i]][1]))
            for k in range(len(distance)):
                distance[k] = np.linalg.norm(this_matrix[:,k])
            indices_to_add = np.argsort(distance)
            if i==0:
                snapshots_to_add.append(sub_snapshots[neighbors[j][i]][:,indices_to_add[:N_add]])
            else:
                snapshots_to_add[j] =  np.c_[ snapshots_to_add[j] , sub_snapshots[neighbors[j][i]][:,indices_to_add[:N_add]] ]

    for j in range(solution_manifold_clusters):
        sub_snapshots[j] = np.c_[sub_snapshots[j], snapshots_to_add[j]]
        print(f'{j}\'th  sub-snapshot contains',(np.shape(sub_snapshots[j])[1]), 'columns after overlapping')

    return sub_snapshots, correct_cluster

"""



"""
This is wrong, but save for now as reference
def narrowing_clustering(S, narrowing, narrowing_clusters = 3, overlaping_snapshots = 1 ):
    # wrong implementation :(
    # MINE (no k-means)
    #S = np.load('SnapshotMatrix.npy')
    total_snapshots = S.shape[1]
    #narrowing = np.load('narrowing.npy')
    MAX = np.max(narrowing)
    MIN = np.min(narrowing)
    print('the maximum is ',MAX, ' and the minimum is: ', MIN)
    sub_snapshots = {}
    step = (MAX - MIN)/ (narrowing_clusters + 1)
    correct_cluster = np.empty(narrowing.shape)
    for i in range(narrowing_clusters):
        # In this implementation, I just shuffle (order) the snapshots to match the narrowing width. No time-relation whatsoever
        lower_bounds = np.where(narrowing > (MIN + (step*(i) )))[0]
        uppper_bounds  = np.where(narrowing < (MIN + (step*(i+1) )))[0]
        intersection = np.intersect1d(lower_bounds, uppper_bounds)
        correct_cluster[intersection] = i
        ith_narrowing = narrowing[intersection]
        ith_indexes_ordered = np.argsort(ith_narrowing)
        sub_snapshots[i] = S[:,ith_indexes_ordered]
        print(f'the {i}th subsnapsht has shape: ',sub_snapshots[i].shape)
        print('with minimum value: ',np.min(narrowing[intersection]))
        print('with maximum value: ', np.max(narrowing[intersection]),'\n')
        # storing centroids
        if i==0:
            centroids = np.sum(ith_narrowing)/(ith_narrowing.shape[0])
        else:
            centroids = np.c_[centroids, np.sum(ith_narrowing)/(ith_narrowing.shape[0])]
    np.save('cluster_centroid.npy', centroids)
    #overlapping after correct cluster definition

    #get list containing snapshots to add to each overlapped cluster
    snapshots_to_add = {}
    for i in range(narrowing_clusters):
        if i == 0:
            snapshots_to_add[0] = sub_snapshots[1][:,:overlaping_snapshots]
        elif i == narrowing_clusters-1:
            snapshots_to_add[i] = sub_snapshots[i-1][:, -overlaping_snapshots:]
        else:
            snapshots_to_add[i] = sub_snapshots[i-1][:, -overlaping_snapshots:]
            snapshots_to_add[i] = np.c_[snapshots_to_add[i], sub_snapshots[i+1][:, :overlaping_snapshots] ]

    #actually enlarging sub_snapshots
    for j in range(narrowing_clusters):
        sub_snapshots[j] = np.c_[sub_snapshots[j], snapshots_to_add[j]]
        print(f'{j}\'th  sub-snapshot contains',(np.shape(sub_snapshots[j])[1]), 'columns after overlapping')

    return sub_snapshots, correct_cluster

"""


"""
def time_clustering(time_clusters = 5, overlaping_snapshots = 1 ):
    #it works, but no overlapping
    S = np.load('SnapshotMatrix.npy')
    total_time_steps = S.shape[1]
    if time_clusters > total_time_steps:
        raise error
    sub_snapshots = np.array_split(S,time_clusters, axis=1)

    for i in range(time_clusters):
        if i == 0:
            correct_cluster = np.full((sub_snapshots[0].shape[1],), 0 )
        else:
            correct_cluster = np.r_[correct_cluster, np.full((sub_snapshots[i].shape[1],), i )]

    return sub_snapshots, correct_cluster
"""


"""
def narrowing_clustering(narrowing_clusters = 3, overlaping_snapshots = 1 ):
    #no overlapping. MINE (no k-means)
    S = np.load('SnapshotMatrix.npy')
    total_snapshots = S.shape[1]
    narrowing = np.load('narrowing.npy')
    MAX = np.max(narrowing)
    MIN = np.min(narrowing)
    print('the maximum is ',MAX, ' and the minimum is: ', MIN)
    sub_snapshots = {}
    step = (MAX - MIN)/ (narrowing_clusters + 1)
    for i in range(narrowing_clusters):
        lower_bounds = np.where(narrowing > (MIN + (step*(i) )))[0]
        uppper_bounds  = np.where(narrowing < (MIN + (step*(i+1) )))[0]
        intersection = np.intersect1d(lower_bounds, uppper_bounds)
        sub_snapshots[i] = S[:,intersection]
        if i == 0:
            correct_cluster = np.full((sub_snapshots[0].shape[1],), 0 )
        else:
            correct_cluster = np.r_[correct_cluster, np.full((sub_snapshots[i].shape[1],), i )]
        print(f'the {i}th subsnapsht has shape: ',sub_snapshots[i].shape)
        print('with minimum value: ',np.min(narrowing[intersection]))
        print('with maximum value: ', np.max(narrowing[intersection]),'\n')

    return sub_snapshots, correct_cluster
"""

"""
def narrowing_clustering(narrowing_clusters = 3, overlaping_snapshots = 1 ):
    # MINE (no k-means)
    S = np.load('SnapshotMatrix.npy')
    total_snapshots = S.shape[1]
    narrowing = np.load('narrowing.npy')
    MAX = np.max(narrowing)
    MIN = np.min(narrowing)
    print('the maximum is ',MAX, ' and the minimum is: ', MIN)
    sub_snapshots = {}
    step = (MAX - MIN)/ (narrowing_clusters + 1)
    for i in range(narrowing_clusters):
        lower_bounds = np.where(narrowing > (MIN + (step*(i) )))[0]
        uppper_bounds  = np.where(narrowing < (MIN + (step*(i+1) )))[0]
        intersection = np.intersect1d(lower_bounds, uppper_bounds)
        sub_snapshots[i] = S[:,intersection]
        if i == 0:
            correct_cluster = np.full((sub_snapshots[0].shape[1],), 0 )
        else:
            correct_cluster = np.r_[correct_cluster, np.full((sub_snapshots[i].shape[1],), i )]
        print(f'the {i}th subsnapsht has shape: ',sub_snapshots[i].shape)
        print('with minimum value: ',np.min(narrowing[intersection]))
        print('with maximum value: ', np.max(narrowing[intersection]),'\n')

    #overlapping after correct cluster definition
    # In this implementation, I just shuffle the snapshots to match the narrowing width. No time relation whatsoever
    for i in range(narrowing_clusters):
        lower_bounds = np.where(narrowing > (MIN + (step*(i) )))[0]
        uppper_bounds  = np.where(narrowing < (MIN + (step*(i+1) )))[0]
        intersection = np.intersect1d(lower_bounds, uppper_bounds)
        if i == 0:
            ith_narrowing = narrowing[intersection]

            ith_indexes = np.argsort(ith_narrowing)
            ith_narrowing_ordered = ith_narrowing[ith_indexes]
            plt.plot(ith_narrowing, 'b')
            plt.plot(ith_narrowing_ordered, 'r')
            plt.show()

        elif i == narrowing_clusters-1:
            sub_snapshots[i] = np.c_[sub_snapshots[i-1][:, -overlaping_snapshots:], sub_snapshots[i]]
        else:
            sub_snapshots[i] = np.c_[sub_snapshots[i-1][:, -overlaping_snapshots:], sub_snapshots[i]]
            sub_snapshots[i] = np.c_[sub_snapshots[i] , sub_snapshots[i+1][:, :overlaping_snapshots] ]
        print(f'{i}\'th  sub-snapshot contains',(np.shape(sub_snapshots[i])[1]), 'columns after overlapping')

    return sub_snapshots, correct_cluster
"""

