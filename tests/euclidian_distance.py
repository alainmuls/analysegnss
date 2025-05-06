import numpy

import perfplot

# from scipy.spatial import distance


def linalg_norm(data):
    a, b = data[0]
    return numpy.linalg.norm(a - b)


def linalg_norm_T(data):
    a, b = data[1]
    return numpy.linalg.norm(a - b)


def sqrt_sum(data):
    a, b = data[0]
    return numpy.sqrt(numpy.sum((a - b) ** 2, axis=1))


def sqrt_sum_T(data):
    a, b = data[1]
    return numpy.sqrt(numpy.sum((a - b) ** 2, axis=0))


# def scipy_distance(data):
#     a, b = data[0]
#     return list(map(distance.euclidean, a, b))


def sqrt_einsum(data):
    a, b = data[0]
    a_min_b = a - b
    return numpy.sqrt(numpy.einsum("ij,ij->i", a_min_b, a_min_b))


def sqrt_einsum_T(data):
    a, b = data[1]
    a_min_b = a - b
    return numpy.sqrt(numpy.einsum("ij,ij->j", a_min_b, a_min_b))


def setup(n):
    a = numpy.random.rand(n, 3)
    b = numpy.random.rand(n, 3)
    out0 = numpy.array([a, b])
    out1 = numpy.array([a.T, b.T])
    return out0, out1


b = perfplot.bench(
    setup=setup,
    n_range=[2**k for k in range(22)],
    kernels=[
        linalg_norm,
        linalg_norm_T,
        # scipy_distance,
        sqrt_sum,
        sqrt_sum_T,
        sqrt_einsum,
        sqrt_einsum_T,
    ],
    xlabel="len(x), len(y)",
)
b.save("norm.png")
