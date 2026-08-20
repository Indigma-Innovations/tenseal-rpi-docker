import tenseal as ts

context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60],
)
context.global_scale = 2**40

encrypted = ts.ckks_vector(context, [10.0, 20.0])
result = encrypted * 2

print(result.decrypt())

